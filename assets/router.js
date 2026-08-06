/* Client half of the router. Server half is docrender/router.py, and the
 * crypto it pairs with is docrender/seal.py.
 *
 * WARNING: THIS FILE AND docrender/seal.py SHARE THE KDF AND THE ITERATION
 * COUNT. Change one without the other and every router silently stops working,
 * with no error a reader could act on. They move in the same PR, always. The
 * count is read off a data attribute so there is one source for it -- but the
 * pairing still has to be verified, because a mismatch is invisible.
 *
 * TWO THINGS ON A PAGE, AND SINCE 2026-08-06 THEY ARE INDEPENDENT:
 *
 *   .dr-router     the FORM. Only where a router is declared or inherited.
 *   .dr-nav-boot   the SEALED SIDEBAR. On every page of the site.
 *
 * THAT SPLIT IS THE FIX FOR "IT DISAPPEARS AFTER I ENTER THE CODE". The nav
 * payload used to be an attribute of the form, so a reader who unlocked a
 * folder and clicked into it landed on a page with no ciphertext and watched
 * the folder vanish from the sidebar. Every guard in this file assumed the form
 * existed.
 *
 * TWO FORM MODES, read off `data-mode`:
 *
 *   curtain   the page's own body is sitting hidden in the DOM. Verify the
 *             code against a PBKDF2 verifier and reveal it in place.
 *   redirect  each destination is sealed under its key. Try the code against
 *             each until one decrypts, then navigate there.
 *
 * Why curtain verifies instead of decrypting: there is nothing to decrypt. The
 * body is hidden, not encrypted -- deliberately, because the markdown is in the
 * content repo and encrypting it would be theatre. What the verifier buys is
 * that the page does not hand out the CODE.
 *
 * AND TWO THINGS THAT ARE GENUINELY SEALED: redirect destinations, and THE NAV
 * MANIFEST (DL J14).
 *
 * =========================================================================
 * NOTHING WARM COSTS CRYPTO. THAT IS THE WHOLE PERFORMANCE DESIGN (DL J17)
 * =========================================================================
 * Michael, on the version before this one: "it's still like loading the menu
 * each time and passing it immediately which seems like bad architecture."
 *
 * It was. Every page minted its own salt, so a code already typed had to be
 * re-derived at 120,000 iterations on arrival, per key, in sequence, while the
 * reader watched. The salt is stable per build now, so:
 *
 *   THE BODY   router.py's inline boot script compares a cached verifier before
 *              first paint and sets `dr-open`. No derivation on that path.
 *   THE NAV    the DECRYPTED manifest is cached in sessionStorage under the
 *              build id, so page two draws the sidebar with no crypto at all.
 *
 * WARNING: WHAT IS CACHED IS NOT A SECRET. The verifier is printed in the page
 * it unlocks, and the manifest is content this reader has already been shown.
 * The CODE itself is in sessionStorage either way and has been since this file
 * was written. All of it dies with the tab, which is the point on a shared
 * machine in a shop or a booth.
 */

(function () {
  var STORE = 'docrender.keys';
  var LIMIT = 8;                 // keeps the worst-case derivation count sane

  var boot = document.querySelector('.dr-nav-boot');
  var form = document.querySelector('.dr-router');
  if (!boot && !form) return;
  if (!window.crypto || !crypto.subtle) return;

  /* WARNING: READ FROM WHICHEVER ELEMENT EXISTS. A page outside a routed folder
   * has no form, and this used to be `form.dataset.iter` unconditionally. */
  var iterations = parseInt(
    (form && form.dataset.iter) || (boot && boot.dataset.iter), 10
  );
  var root = document.documentElement;

  var input = form && form.querySelector('.dr-router__input');
  var button = form && form.querySelector('.dr-router__btn');
  var error = form && form.querySelector('.dr-router__error');
  var curtain = document.querySelector('.dr-curtain');

  function bytes(s) {
    return Uint8Array.from(atob(s), function (c) { return c.charCodeAt(0); });
  }

  function b64(buffer) {
    var view = new Uint8Array(buffer);
    var out = '';
    for (var i = 0; i < view.length; i++) out += String.fromCharCode(view[i]);
    return btoa(out);
  }

  function decode(attr) {
    try {
      return JSON.parse(atob(attr)) || [];
    } catch (e) {
      return [];
    }
  }

  function routes() {
    return form ? decode(form.dataset.routes) : [];
  }

  /* Held keys, normalised. An entry is {k: code, s: salt, h: verifier}, where
   * s and h are absent until a code has been proven once.
   *
   * WARNING: TOLERATES THE OLD FORMAT ON PURPOSE. This store used to be a list
   * of bare code strings, and a reader can be mid-session when a deploy lands.
   * A string becomes {k: string} with no cached verifier, which is the slow
   * path -- correct, just not warm. Dropping them instead would log somebody
   * out mid-visit for a reason they could never work out. */
  function held() {
    var raw;
    try {
      raw = JSON.parse(sessionStorage.getItem(STORE));
    } catch (e) {
      return [];
    }
    if (!Array.isArray(raw)) return [];
    return raw.map(function (e) {
      return typeof e === 'string' ? { k: e } : e;
    }).filter(function (e) { return e && e.k; });
  }

  function remember(code, entry) {
    var keep = { k: code };
    /* Only a CURTAIN verifier is cacheable. A redirect entry has no `h`, and
     * caching its salt would let the warm path claim a match that proves
     * nothing about this page. */
    if (entry && entry.h) {
      keep.s = entry.s;
      keep.h = entry.h;
    }
    var keys = held().filter(function (e) { return e.k !== code; });
    keys.unshift(keep);
    try {
      sessionStorage.setItem(STORE, JSON.stringify(keys.slice(0, LIMIT)));
    } catch (e) { /* private mode: unlocking works, it just is not sticky */ }
  }

  /* The code whose cached verifier matched an entry on THIS page. The boot
   * script proved a match but cannot hand us a value, so we recompute which
   * one it was -- string comparisons, no crypto. */
  function warmCode() {
    var all = routes();
    var keys = held();
    for (var i = 0; i < keys.length; i++) {
      var c = keys[i];
      if (!c.h) continue;
      for (var j = 0; j < all.length; j++) {
        if (all[j].h && all[j].s === c.s && all[j].h === c.h) return c.k;
      }
    }
    return null;
  }

  function derive(code, salt, usage) {
    return crypto.subtle.importKey(
      'raw', new TextEncoder().encode(code), 'PBKDF2', false,
      ['deriveKey', 'deriveBits']
    ).then(function (material) {
      if (usage === 'bits') {
        return crypto.subtle.deriveBits(
          { name: 'PBKDF2', salt: bytes(salt), iterations: iterations,
            hash: 'SHA-256' },
          material, 256
        );
      }
      return crypto.subtle.deriveKey(
        { name: 'PBKDF2', salt: bytes(salt), iterations: iterations,
          hash: 'SHA-256' },
        material, { name: 'AES-GCM', length: 256 }, false, ['decrypt']
      );
    });
  }

  function open(code, entry) {
    return derive(code, entry.s).then(function (key) {
      return crypto.subtle.decrypt(
        { name: 'AES-GCM', iv: bytes(entry.n) }, key, bytes(entry.w)
      );
    }).then(function (plain) {
      return new TextDecoder().decode(plain);
    });
  }

  /* One code against every entry on the FORM, sequentially. A curtain entry has
   * a verifier to match; a redirect entry has a sealed destination to decrypt.
   * Sequential on purpose: the common case is a handful of keys, and firing
   * every PBKDF2 at once would burn a phone's battery to save nothing. */
  function resolve(code) {
    var all = routes();

    function attempt(i) {
      if (i >= all.length) return Promise.reject(new Error('no route'));
      var entry = all[i];
      var next = function () { return attempt(i + 1); };

      if (entry.h) {
        return derive(code, entry.s, 'bits').then(function (raw) {
          /* The code and the matched entry both travel with the result: the
           * code because the nav manifest is sealed under it and a verifier
           * cannot be reversed, the entry because its salt and verifier are
           * what get cached for the warm path. */
          if (b64(raw) === entry.h) {
            return { reveal: true, code: code, entry: entry };
          }
          return next();
        }).catch(next);
      }

      return open(code, entry).then(function (plain) {
        return { go: plain };
      }).catch(next);
    }

    return attempt(0);
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

  /* A code has just been proven. Decrypt whatever it opens, remember it, and
   * draw it MOVING -- because something did just happen. */
  function unlockNav(code) {
    var entries = navEntries();
    if (!entries.length || !code) return;

    var already = drawn();
    var opened = [];

    function nextEntry(i) {
      if (i >= entries.length) {
        if (!opened.length) return;
        keepDrawn(already.concat(opened));
        paint(opened, true);
        return;
      }
      var entry = entries[i];
      var wraps = entry.w || [];

      function nextWrap(j) {
        if (j >= wraps.length) return nextEntry(i + 1);
        return open(code, wraps[j]).then(function (plain) {
          try {
            opened.push({
              p: entry.p, a: entry.a, b: entry.b, i: entry.i,
              items: JSON.parse(plain)
            });
          } catch (e) { /* a manifest we cannot parse reveals nothing */ }
          nextEntry(i + 1);
        }).catch(function () { nextWrap(j + 1); });
      }

      nextWrap(0);
    }

    nextEntry(0);
  }

  /* ARRIVAL, for the sidebar. Runs on every page of the site.
   *
   * THE CACHED PATH DOES NOT ANIMATE, and that is a real distinction rather
   * than a detail: a reader navigating inside a folder they already opened
   * should find it simply THERE. Re-animating on every page is the twitch the
   * pre-paint boot script exists to prevent. The old code could not tell these
   * apart -- it keyed the suppression off `.dr-open`, which is set by the FORM,
   * and pages outside the folder have no form. */
  if (boot) {
    var cached = drawn();
    if (cached.length) {
      paint(cached, false);
    } else {
      /* COLD. Nothing cached for this build, so held codes have to be tried
       * once. Happens on the first page after an unlock elsewhere, or the first
       * page after a deploy moved the build id -- never on a steady session. */
      held().forEach(function (entry) { unlockNav(entry.k); });
    }
  }

  /* ======================================================================
   * THE FORM
   * =================================================================== */
  if (!form) return;

  function apply(result) {
    if (result.go) {
      window.location.href = result.go;
      return;
    }
    if (curtain) {
      curtain.hidden = false;
      unlockNav(result.code);
      form.remove();
    }
  }

  form.addEventListener('submit', function (e) {
    e.preventDefault();
    var code = input.value.trim();
    if (!code) return;

    error.hidden = true;
    button.disabled = true;
    button.textContent = 'Checking';

    resolve(code).then(function (result) {
      remember(code, result.entry);
      apply(result);
    }).catch(function () {
      error.hidden = false;
      input.value = '';
      input.focus();
      button.disabled = false;
      button.textContent = 'Go';
    });
  });

  /* Only curtains open by themselves. Silently redirecting somebody who just
   * arrived would be hostile -- they did not ask to go anywhere. */
  if (!curtain) return;

  /* WARM. The boot script already proved a cached verifier matches, so the body
   * is showing and the form is hidden -- both from CSS, before paint. Nothing
   * here re-derives anything; it finishes the job by dropping the `hidden`
   * attribute (CSS was only overriding its DISPLAY, and assistive technology
   * reads the attribute) and taking the dead form out.
   *
   * WARNING: `dr-open` IS DELIBERATELY LEFT ON <html>. Removing it looks like
   * tidying up and would reintroduce the exact flash this whole change removes:
   * the curtain's fade-in keys off `.dr-curtain:not([hidden])`, which starts
   * matching the moment the line below runs, so a body that was already on
   * screen would animate in a second time. */
  if (root.classList.contains('dr-open')) {
    curtain.hidden = false;
    if (!drawn().length) unlockNav(warmCode());
    form.remove();
    return;
  }

  /* COLD, with keys held. Nothing is cached for this page's salt, so the trial
   * has to run. `dr-checking` is holding the form back; it comes off whether we
   * succeed or fail, because a form nobody can see is worse than a flash. */
  var keys = held();
  if (!keys.length) {
    root.classList.remove('dr-checking');
    return;
  }

  (function tryKey(i) {
    if (i >= keys.length) {
      root.classList.remove('dr-checking');
      return;
    }
    resolve(keys[i].k).then(function (result) {
      if (result.reveal) {
        /* Cache it now. This is the ONLY place a code held from a previous
         * page gets its verifier, so without this line every navigation after
         * a deploy would stay on the cold path forever. */
        remember(keys[i].k, result.entry);
        root.classList.remove('dr-checking');
        return apply(result);
      }
      tryKey(i + 1);
    }).catch(function () {
      tryKey(i + 1);
    });
  })(0);
})();
