/* Client half of the router. Server half is docrender/router.py, and the
 * crypto it pairs with is docrender/seal.py.
 *
 * ⚠️ THIS FILE AND docrender/seal.py SHARE THE KDF AND THE ITERATION COUNT.
 * Change one without the other and every router silently stops working, with no
 * error a reader could act on. They move in the same PR, always. The count is
 * read off `data-iter` rather than hardcoded here, so there is one source for
 * it -- but the pairing still has to be verified, because a mismatch is
 * invisible.
 *
 * TWO MODES, read off `data-mode`:
 *
 *   curtain   the page's own body is sitting hidden in the DOM. Verify the
 *             code against a PBKDF2 verifier and reveal it in place.
 *   redirect  each destination is sealed under its key. Try the code against
 *             each until one decrypts, then navigate there.
 *
 * Why curtain verifies instead of decrypting: there is nothing to decrypt. The
 * body is hidden, not encrypted -- deliberately, because the markdown is public
 * in the content repo and encrypting it would be theatre. What the verifier
 * buys is that the page does not hand out the CODE.
 *
 * AND TWO THINGS THAT ARE GENUINELY SEALED: redirect destinations, and THE NAV
 * MANIFEST (DL J14). A routed folder's children are removed from the sidebar at
 * build time and the list of them ships as ciphertext in `data-subtree`. The
 * code that opens the curtain decrypts it and the entries are injected under
 * the section's own sidebar link.
 *
 * =========================================================================
 * THE WARM PATH: A HELD CODE COSTS NO CRYPTO AT ALL (DL J17)
 * =========================================================================
 * Michael, on the version before this one: "it's still like loading the menu
 * each time and passing it immediately which seems like bad architecture."
 *
 * It was. Every page used to mint its own salt, so a code already typed had to
 * be re-derived at 120,000 iterations on arrival, per key, in sequence, while
 * the reader watched. Now the salt is stable per build, so the DERIVED VERIFIER
 * is cached beside the code and a later page is a string comparison.
 * router.py's inline `_BOOT` script does that comparison BEFORE FIRST PAINT and
 * leaves us one of two classes on <html>:
 *
 *   dr-open      already proven. Reveal, inject nav, remove the form. No
 *                derivation runs on this path at all.
 *   dr-checking  keys held, none cached (first unlock of the session, or the
 *                first page after a deploy moved the salt). Form held back
 *                while we derive; we put it back if every key fails.
 *
 * ⚠️ WHAT IS CACHED IS NOT A SECRET. The verifier is printed in the page it
 * unlocks -- caching it stores something already public. The CODE is in
 * sessionStorage either way, and has been since this file was written.
 *
 * sessionStorage, not localStorage: closing the tab re-locks, because a shared
 * machine in a shop or a booth is the normal case here.
 */

(function () {
  var STORE = 'docrender.keys';
  var LIMIT = 8;                 // keeps the worst-case derivation count sane

  var form = document.querySelector('.dr-router');
  if (!form || !window.crypto || !crypto.subtle) return;

  var input = form.querySelector('.dr-router__input');
  var button = form.querySelector('.dr-router__btn');
  var error = form.querySelector('.dr-router__error');
  var curtain = document.querySelector('.dr-curtain');
  var iterations = parseInt(form.dataset.iter, 10);
  var root = document.documentElement;

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
    return decode(form.dataset.routes);
  }

  /* Held keys, normalised. An entry is {k: code, s: salt, h: verifier}, where
   * s and h are absent until a code has been proven once.
   *
   * ⚠️ TOLERATES THE OLD FORMAT ON PURPOSE. This store used to be a list of
   * bare code strings, and a reader can be mid-session when a deploy lands. A
   * string becomes {k: string} with no cached verifier, which is the slow path
   * -- correct, just not warm. Dropping them instead would log somebody out
   * mid-visit for a reason they could never work out. */
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
      'raw', new TextEncoder().encode(code), 'PBKDF2', false, ['deriveKey', 'deriveBits']
    ).then(function (material) {
      if (usage === 'bits') {
        return crypto.subtle.deriveBits(
          { name: 'PBKDF2', salt: bytes(salt), iterations: iterations, hash: 'SHA-256' },
          material, 256
        );
      }
      return crypto.subtle.deriveKey(
        { name: 'PBKDF2', salt: bytes(salt), iterations: iterations, hash: 'SHA-256' },
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

  /* One code against every entry, sequentially. A curtain entry has a verifier
   * to match; a redirect entry has a sealed destination to decrypt. Sequential
   * on purpose: the common case is a handful of keys, and firing every PBKDF2
   * at once would burn a phone's battery to save nothing measurable. */
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
          if (b64(raw) === entry.h) return { reveal: true, code: code, entry: entry };
          return next();
        }).catch(next);
      }

      return open(code, entry).then(function (plain) {
        return { go: plain };
      }).catch(next);
    }

    return attempt(0);
  }

  /* ------------------------------------------------------------------------
   * THE SIDEBAR
   *
   * The entries were removed from the nav at build time, so there is nothing
   * to un-hide -- they have to be built. Rendered with our own classes rather
   * than Material's nested-nav markup, which needs a <nav>, a <label> and a
   * hidden checkbox per level to work its expand/collapse machinery. We are
   * inserting a flat list into an already-rendered tree; borrowing half of
   * that structure would inherit its behaviour and none of its state.
   *
   * ⚠️ AND ON MOBILE THAT IS NOT MERELY A PREFERENCE. Material's drawer is a
   * stack of sliding panels: a nested `<nav class="md-nav">` is positioned
   * OFF-CANVAS until its toggle is checked. Injecting one into a section whose
   * children were sealed -- so it is no longer marked `--nested` and has no
   * toggle -- would put the menu somewhere no reader can reach, on phones only.
   * --------------------------------------------------------------------- */

  function navAnchor() {
    var href = form.dataset.subtreeAnchor;
    if (!href) return null;

    /* Scoped to the PRIMARY nav on purpose. The secondary nav is the
     * table of contents, whose links are #fragments on the current page --
     * so on the routed index page itself their pathname matches the anchor
     * exactly, and an unscoped search would inject the menu into the TOC. */
    var want = new URL(href, window.location.href).pathname;
    var links = document.querySelectorAll('.md-nav--primary a.md-nav__link');
    for (var i = 0; i < links.length; i++) {
      if (new URL(links[i].href).pathname === want) return links[i];
    }
    return null;
  }

  function drawNav(items) {
    var link = navAnchor();
    if (!link || !items.length) {
      /* Said out loud rather than returning quietly. A correct code that
       * reveals the body and silently leaves the menu empty is exactly the
       * kind of half-working feature this engine keeps digging out. */
      if (!link) console.warn('docrender: nav anchor not found, menu not restored');
      return;
    }

    /* 🔴 THE LIST HANGS OFF THE <li>, NOT OFF THE LINK'S PARENT. Getting this
     * wrong is what shipped in #48 and it looked spectacular on a phone.
     *
     * With `navigation.indexes` enabled, Material wraps a section's index link
     * in `<div class="md-nav__link md-nav__container">`, and that container is
     * `display: flex`. `link.parentNode` IS that container, so appending here
     * made the revealed menu a third FLEX ITEM beside the title and the
     * chevron: the section name squeezed into a two-line column, the chevron
     * pushed out of the row, and every entry marching further right as its
     * depth padding compounded inside a column a few characters wide.
     *
     * ⚠️ IT ALSO INHERITED THE WRONG TYPE, FOR FREE, WHICH IS THE PART WORTH
     * REMEMBERING. `text-transform`, `letter-spacing` and `font-weight` are
     * INHERITED properties, and that container matches base.css's top-level
     * caps rule. So the child pages rendered in bold 700 uppercase -- shouting
     * louder than the section heading above them. Nothing chose that and no
     * rule in router.css said it; it fell through the DOM. Hoisting one level
     * fixes the layout and the typography in the same move, because the <li>
     * carries neither property. */
    var host = link.closest('.md-nav__item') || link.parentNode;
    if (host.querySelector('.dr-nav-revealed')) return;

    var list = document.createElement('ul');
    list.className = 'dr-nav-revealed';

    items.forEach(function (item) {
      var row = document.createElement('li');
      row.className = 'dr-nav-revealed__item';
      row.setAttribute('data-d', String(item.d || 1));

      /* An entry with no url is a folder heading, not a destination. */
      var cell = document.createElement(item.u ? 'a' : 'span');
      cell.className = 'dr-nav-revealed__link';
      cell.textContent = item.t;
      if (item.u) cell.href = item.u;

      row.appendChild(cell);
      list.appendChild(row);
    });

    host.appendChild(list);
  }

  function revealNav(code) {
    var wraps = form.dataset.subtree ? decode(form.dataset.subtree) : [];
    if (!wraps.length || !code) return;

    (function attempt(i) {
      if (i >= wraps.length) return;
      open(code, wraps[i]).then(function (plain) {
        try {
          drawNav(JSON.parse(plain));
        } catch (e) { /* a manifest we cannot parse reveals nothing */ }
      }).catch(function () {
        attempt(i + 1);
      });
    })(0);
  }

  function apply(result) {
    if (result.go) {
      window.location.href = result.go;
      return;
    }
    if (curtain) {
      curtain.hidden = false;
      revealNav(result.code);
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

  /* ------------------------------------------------------------------------
   * ARRIVAL
   *
   * Only curtains open by themselves. Silently redirecting somebody who just
   * arrived would be hostile -- they did not ask to go anywhere.
   *
   * This is also what carries the revealed MENU across a folder: every page
   * under a routed index inherits the router, so each ships its own sealed
   * manifest, and a held code re-injects the sidebar on arrival. A page OUTSIDE
   * the routed folder has no form and therefore no manifest, so the section
   * collapses again out there -- the known limit, written up in
   * docrender/visibility.py.
   * --------------------------------------------------------------------- */
  if (!curtain) return;

  /* WARM. The boot script already proved a cached verifier matches, so the body
   * is showing and the form is hidden -- both from CSS, before paint. Nothing
   * here re-derives anything; it finishes the job by dropping the `hidden`
   * attribute (CSS was only overriding its DISPLAY, and assistive technology
   * reads the attribute), decrypting the nav, and taking the dead form out.
   *
   * ⚠️ `dr-open` IS DELIBERATELY LEFT ON <html>. Removing it looks like tidying
   * up and would reintroduce the exact flash this whole change removes: the
   * curtain's fade-in keys off `.dr-curtain:not([hidden])`, which starts
   * matching the moment the line below runs, so a body that was already on
   * screen would animate in a second time. router.css suppresses that with a
   * `.dr-open` rule, and a class removed in the same tick cannot be relied on
   * to still be there when style is recalculated. */
  if (root.classList.contains('dr-open')) {
    curtain.hidden = false;
    revealNav(warmCode());
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
