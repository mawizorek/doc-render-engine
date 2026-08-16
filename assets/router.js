/* Client half of the router. Server half is docrender/router.py, and the
 * crypto it pairs with is docrender/seal.py.
 *
 * ⚠️ THE SIDEBAR HALF NOW LIVES IN assets/navtree.js (split 2026-08-16 at
 * 22,232 B, past the 22KB hard read limit). This file owns the FORM, the
 * crypto, and the held codes; that one owns everything that DRAWS the revealed
 * menu. It is loaded FIRST -- see docrender/assets.py `_FEATURE_ASSETS` -- and
 * is read into `tree` below with a null guard, so a site that somehow ships
 * without it still unlocks pages and only loses the sidebar injection.
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

  /* The sidebar renderer, assets/navtree.js. Read into a local and guarded at
   * every call site: no navtree means no injected menu, never a dead form. */
  var tree = window.docrenderNavTree || null;

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

  /* ⚠️ navtree.js carries its own copy of this, on purpose. See the note there:
   * a base64-JSON reader is a primitive with no behaviour to drift, and sharing
   * it would make the FORM fail when the SIDEBAR file is missing. */
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

  /* A code has just been proven. Decrypt whatever it opens, remember it, and
   * draw it MOVING -- because something did just happen.
   *
   * The decryption is here and the DRAWING is in navtree.js: this function is
   * the seam between the two files, and it is the only place plaintext crosses
   * it. */
  function unlockNav(code) {
    if (!tree) return;
    var entries = tree.entries();
    if (!entries.length || !code) return;

    var already = tree.drawn();
    var opened = [];

    function nextEntry(i) {
      if (i >= entries.length) {
        if (!opened.length) return;
        tree.keepDrawn(already.concat(opened));
        tree.paint(opened, true);
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
  if (boot && tree) {
    var cached = tree.drawn();
    if (cached.length) {
      tree.paint(cached, false);
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
    if (tree && !tree.drawn().length) unlockNav(warmCode());
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
