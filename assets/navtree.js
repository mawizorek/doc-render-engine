/* The SIDEBAR half of the router. Split out of assets/router.js 2026-08-16 at
 * 22,232 B, past the engine's 22KB hard read limit, in the commit before this
 * one. Styling is assets/navtree.css, split from router.css on the same seam.
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
 * contract, and it is why the split needed no shared crypto module.
 *
 * ⚠️ LOADS BEFORE router.js. The order is set in docrender/assets.py
 * `_FEATURE_ASSETS` and is NOT alphabetical -- router.js calls into this file
 * during its own IIFE, so a later position makes every call a TypeError on the
 * first paint. ⭐ A MISSING navtree.js is safe (router.js guards the reference
 * and only the sidebar goes quiet); a MIS-ORDERED one is a dead sidebar, and no
 * guard can fix an order.
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
 *
 * =========================================================================
 * ⭐ THE REVEALED MENU IS A TREE, AND IT IS CLOSED UNTIL YOU ARE IN IT
 * =========================================================================
 * Michael, 2026-08-16: *"the doc renderer page navigation index is a bit weird
 * - and ends up auto-expanding like entirely after entering some routers. it's
 * not good and not useful."*
 *
 * He was describing three deliberate decisions compounding into one nobody made:
 *
 *   1. the revealed list was FLAT and rendered in full at every depth
 *   2. it repaints on EVERY page of the site for the rest of the session
 *   3. it STACKED -- one more full dump per code held
 *
 * And `navigation.prune` is ON, so every folder the reader is NOT inside shows
 * no children at all. The unlocked folder was therefore the single loudest thing
 * in the sidebar, permanently, which is the opposite of what unlocking should
 * feel like. ⭐ Fixing (1) defuses (2) and (3) on its own: two codes are now two
 * tidy closed rows instead of two walls.
 *
 * 🔴 WHY THE OLD CODE WAS FLAT, AND WHY THAT REASON NEVER APPLIED TO THIS.
 * The standing rule -- still true, still enforced below -- is that a revealed
 * list must NOT borrow Material's nested-nav markup: a nested
 * `<nav class="md-nav">` is positioned OFF-CANVAS until its toggle is checked,
 * and a sealed section is no longer `--nested` and has no toggle, so the menu
 * would land somewhere no phone can reach. ⚠️ THAT IS A RULE ABOUT MATERIAL'S
 * MARKUP, NOT ABOUT THE IDEA OF COLLAPSING, and it was read as the second thing
 * for ten days. Own element, own class, own `hidden` attribute: no off-canvas
 * panel, no checkbox, no label, and the drawer never moves.
 *
 * ⭐ COLLAPSED BY DEFAULT WITH THE ACTIVE BRANCH OPEN IS DELIBERATELY THE RULE
 * THE REST OF THE SIDEBAR ALREADY FOLLOWS. Material writes `checked` onto a
 * built section for exactly one reason -- it holds the current page -- and
 * docrender/navstate.py is built directly on top of that. `markPath` below asks
 * the same question and answers it the same way, so an unlocked folder behaves
 * like a BUILT folder instead of like an announcement.
 *
 * ⚠️ THE MANIFEST FORMAT DID NOT CHANGE. It is still flat on the wire, still
 * carrying a depth per entry, and docrender/visibility.py `_collect` still knows
 * nothing about any of this. Nesting happens in the DOM only -- see `nest`.
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
   * Material's nested-nav markup; the header has the whole argument, and the
   * off-canvas warning in it is still live law.
   *
   * TWO PLACEMENTS, read off each entry's `p`:
   *
   *   in   the folder still has its own row. Find it, hoist to its <li>,
   *        hang the menu underneath.
   *   at   `nav: routed` -- the folder is not in the sidebar at all, so entry
   *        ZERO of the manifest is the folder itself and we build its row.
   * =================================================================== */

  /* Flat manifest -> nested nodes. An entry deeper than the one before it is
   * that one's child; anything shallower walks back up the stack.
   *
   * ⭐ THE WIRE FORMAT STAYS FLAT, WHICH WAS ALWAYS THE RIGHT CALL: a flat list
   * cannot be mis-nested by a bug in the injection, and the depth is authored
   * once, server-side, by the walk that actually knows the tree. This turns it
   * back into a shape the DOM can collapse, and it is the ONLY place that
   * arithmetic happens. */
  function nest(items) {
    var roots = [];
    var stack = [];

    items.forEach(function (item) {
      var node = { item: item, kids: [], onPath: false };
      var depth = item.d || 1;

      while (stack.length && stack[stack.length - 1].depth >= depth) stack.pop();
      if (stack.length) stack[stack.length - 1].node.kids.push(node);
      else roots.push(node);

      stack.push({ depth: depth, node: node });
    });

    return roots;
  }

  /* Which rows hold the page the reader is on. Bottom-up in one pass, so a
   * folder learns it is on the path if anything beneath it is.
   *
   * ⭐ THIS IS THE ENTIRE 'COLLAPSED BY DEFAULT' RULE, and it is copied from
   * Material rather than invented -- see the header. Recomputed on every paint
   * from `window.location.pathname`, never cached, so navigating inside an
   * unlocked folder re-opens the right branch and closes the ones you left.
   * Nothing about open state is persisted, deliberately: derived state cannot go
   * stale, and a remembered one would fight the reader on the next page. */
  function markPath(nodes) {
    var any = false;
    nodes.forEach(function (node) {
      var here = !!node.item.u
        && pathOf(siteUrl(node.item.u)) === window.location.pathname;
      var below = markPath(node.kids);
      node.onPath = here || below;
      if (node.onPath) any = true;
    });
    return any;
  }

  function prepare(items) {
    var nodes = nest(items);
    return { nodes: nodes, onPath: markPath(nodes) };
  }

  /* One disclosure, three call sites, and ZERO WRAPPER ELEMENTS -- the absence
   * of a wrapper is the load-bearing part.
   *
   * 🔴 nav.css caps the top level with
   * `.md-nav--primary > .md-nav__list > .md-nav__item > .md-nav__link`, a
   * DIRECT-CHILD chain. Wrapping a row's link in a flex container to sit the
   * button beside it would break that chain, and the injected folder would
   * render in quiet sentence case while every real section next to it shouted --
   * the #48 typography bug arriving from the opposite direction. So the toggle
   * is a SIBLING of the link and navtree.css places it over the row.
   *
   * The handler closes over the two elements it flips rather than looking them
   * up, so nothing here depends on a selector still matching after a future
   * markup change. */
  function hangSub(row, nodes, animate, open, label) {
    var sub = buildFrom(nodes, animate, false);
    sub.hidden = !open;

    var toggle = document.createElement('button');
    toggle.type = 'button';
    toggle.className = 'dr-nav-revealed__toggle';
    toggle.setAttribute('aria-expanded', open ? 'true' : 'false');
    /* A folder heading with no url is a <span> and cannot be clicked, so on
     * those rows this button is the ONLY control and has to name what it opens.
     * Labelled on every row for consistency rather than only where it is
     * strictly required. */
    toggle.setAttribute('aria-label', label || '');

    toggle.addEventListener('click', function () {
      var next = toggle.getAttribute('aria-expanded') !== 'true';
      toggle.setAttribute('aria-expanded', next ? 'true' : 'false');
      sub.hidden = !next;
    });

    /* navtree.css reserves the room for the button off this class. Set here
     * rather than matched with `:has()`, which needs a newer Safari than this
     * engine assumes elsewhere. */
    row.classList.add('dr-nav-parent');
    row.appendChild(toggle);
    row.appendChild(sub);
  }

  /* The revealed list. One builder for every level and both placements, because
   * a second copy of the depth/label/link rules would drift. */
  function buildFrom(nodes, animate, top) {
    var list = document.createElement('ul');
    list.className = 'dr-nav-revealed'
      + (top ? '' : ' dr-nav-revealed--sub')
      + (top && animate ? ' dr-nav-revealed--in' : '');

    nodes.forEach(function (node) {
      var item = node.item;
      var row = document.createElement('li');
      row.className = 'dr-nav-revealed__item';
      row.setAttribute('data-d', String(item.d || 1));

      /* An entry with no url is a folder heading, not a destination. */
      var cell = document.createElement(item.u ? 'a' : 'span');
      cell.className = 'dr-nav-revealed__link';
      cell.textContent = item.t;
      if (item.u) cell.href = siteUrl(item.u);
      row.appendChild(cell);

      if (node.kids.length) {
        hangSub(row, node.kids, animate, node.onPath, item.t);
      }

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
   * the way through lands on the END -- so the floor is the previous behaviour
   * rather than a broken sidebar. */
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
   * sections and has to read as one of them, so it takes their markup -- and
   * `hangSub` is careful not to wrap it, because that markup only works as a
   * direct child. */
  function drawSection(entry, animate) {
    var list = topList();
    if (!list || !entry.items.length) return;

    var head = entry.items[0];
    var key = head.u || head.t;

    /* 🔴 PER FOLDER, NOT PER PAGE. This guard used to be
     * `list.querySelector('.dr-nav-injected')` -- ANY injected row at all -- so
     * a reader holding TWO codes silently never saw the second folder: the first
     * one's row made it look already drawn. Every page under a folder redraws
     * from its own payload, so the guard is still needed; it just has to ask
     * about THIS folder. Compared as DATA rather than built into a selector,
     * because a title is free to contain a quote. */
    var already = list.querySelectorAll('.dr-nav-injected');
    for (var i = 0; i < already.length; i++) {
      if (already[i].getAttribute('data-dr-key') === key) return;
    }

    var li = document.createElement('li');
    li.className = 'md-nav__item dr-nav-injected'
      + (animate ? ' dr-nav-injected--in' : '');
    li.setAttribute('data-dr-key', key);

    var link = document.createElement(head.u ? 'a' : 'span');
    link.className = 'md-nav__link dr-nav-injected__link';
    link.textContent = head.t;
    if (head.u) link.href = siteUrl(head.u);
    li.appendChild(link);

    var rest = entry.items.slice(1);
    if (rest.length) {
      var sub = prepare(rest);
      /* Open when the reader is inside the folder: on one of the revealed pages,
       * or on the folder's own index. Closed everywhere else -- the row still
       * appears site-wide, which is the "sidebar feels dynamic if something
       * unlocks" half, it just no longer shouts its whole contents from three
       * departments away. */
      var inside = sub.onPath
        || (!!head.u && pathOf(siteUrl(head.u)) === window.location.pathname);
      hangSub(li, sub.nodes, animate, inside, head.t);
    }

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

    /* THE MENU HANGS OFF THE <li>, NOT OFF THE LINK'S PARENT. Getting this
     * wrong is what shipped in #48 and it looked spectacular on a phone.
     *
     * With `navigation.indexes` enabled, Material wraps a section's index link
     * in `<div class="md-nav__link md-nav__container">`, and that container is
     * `display: flex`. `link.parentNode` IS that container, so appending there
     * made the revealed menu a third FLEX ITEM beside the title and the
     * chevron.
     *
     * ⚠️ IT ALSO INHERITED THE WRONG TYPE, FOR FREE, WHICH IS THE PART WORTH
     * REMEMBERING. `text-transform`, `letter-spacing` and `font-weight` are
     * INHERITED, and that container matches nav.css's top-level caps rule. So
     * the child pages rendered in bold 700 uppercase, shouting louder than the
     * section above them, with nothing in any stylesheet saying so. Hoisting one
     * level fixes the layout and the typography in one move -- and it is why
     * `hangSub` appends a sibling rather than wrapping anything. */
    var host = link.closest('.md-nav__item') || link.parentNode;
    if (host.querySelector('.dr-nav-revealed')) return;

    var sub = prepare(entry.items);
    /* ⭐ THE SAME TEST `navigation.prune` APPLIES TO EVERY FOLDER THAT WAS NEVER
     * SEALED, which is the whole point: unlocking should hand the reader an
     * ordinary folder, not a wall. Here the folder's own row is Material's and
     * always visible, so a closed disclosure costs nothing -- the reader is one
     * click from the menu on any page of the site. */
    var inside = sub.onPath || pathOf(link.href) === window.location.pathname;
    hangSub(host, sub.nodes, animate, inside, link.textContent);
  }

  /* WHERE THE READER IS. Michael: "notated which page i then nav to."
   *
   * Material's own active class, so an injected row is highlighted exactly like
   * a built one. The SECOND half matters as much as the first: a folder whose
   * CHILD is active is marked too, because clicking into the folder would
   * otherwise take the highlight off the only row that is always on screen. */
  function markActive() {
    var here = window.location.pathname;
    var links = document.querySelectorAll(
      '.dr-nav-revealed__link, .dr-nav-injected__link'
    );

    for (var i = 0; i < links.length; i++) {
      var link = links[i];
      if (link.tagName !== 'A' || pathOf(link.href) !== here) continue;
      link.classList.add('md-nav__link--active');
      link.setAttribute('aria-current', 'page');
      if (!link.classList.contains('dr-nav-revealed__link')) continue;

      /* 🔴 THE FOLDER THAT HOLDS THIS LINK, not the first injected folder in the
       * sidebar. This was `document.querySelector('.dr-nav-injected')`, correct
       * only while a single folder could ever be drawn -- with two codes held it
       * marked the wrong row. A revealed link inside a `place: 'in'` folder has
       * no injected ancestor at all, and `closest` returning null is the right
       * answer there rather than a case to guard. */
      var folder = link.closest('.dr-nav-injected');
      if (folder) folder.classList.add('dr-nav-injected--here');
    }
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
