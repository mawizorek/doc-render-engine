/* Client half of the router. Server half is docrender/router.py.
 *
 * THESE TWO FILES SHARE THE KDF AND THE ITERATION COUNT. Change one without
 * the other and every router silently stops working, with no error a reader
 * could act on. They move in the same PR, always.
 *
 * TWO MODES, read off `data-mode`:
 *
 *   curtain   the page's own body is sitting hidden in the DOM. Verify the
 *             code against a PBKDF2 hash and reveal it in place.
 *   redirect  each destination is sealed under its key. Try the code against
 *             each until one decrypts, then navigate there.
 *
 * Why curtain verifies a hash instead of decrypting: there is nothing to
 * decrypt. The body is hidden, not encrypted -- deliberately, because the
 * markdown is public in the content repo and encrypting it would be theatre.
 * What the hash buys is that the page does not hand out the CODE. See
 * docrender/router.py for the full reasoning.
 *
 * AND ONE THING THAT IS GENUINELY SEALED: THE NAV MANIFEST (DL J14).
 * A routed folder's children are removed from the sidebar at build time, and
 * the list of them ships as ciphertext in `data-subtree`. The code that opens
 * the curtain decrypts it, and the entries are injected under the section's own
 * sidebar link. The body being plaintext and the manifest being sealed is not
 * an inconsistency: the body was never claimed to be protected, whereas a
 * manifest in the clear would defeat the only thing this feature does.
 *
 * An unlock is remembered for the session, so one code opens every curtain it
 * fits. sessionStorage, not localStorage: closing the tab re-locks, because a
 * shared machine in a shop or a booth is the normal case here.
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

  function held() {
    try {
      var keys = JSON.parse(sessionStorage.getItem(STORE));
      return Array.isArray(keys) ? keys : [];
    } catch (e) {
      return [];
    }
  }

  function remember(code) {
    var keys = held().filter(function (k) { return k !== code; });
    keys.unshift(code);
    try {
      sessionStorage.setItem(STORE, JSON.stringify(keys.slice(0, LIMIT)));
    } catch (e) { /* private mode: unlocking works, it just is not sticky */ }
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

  /* One code against every entry, sequentially. A curtain entry has a hash to
   * match; a redirect entry has a sealed destination to decrypt. Sequential on
   * purpose: the common case is a handful of keys, and firing every PBKDF2 at
   * once would burn a phone's battery to save nothing measurable. */
  function resolve(code) {
    var all = routes();

    function attempt(i) {
      if (i >= all.length) return Promise.reject(new Error('no route'));
      var entry = all[i];
      var next = function () { return attempt(i + 1); };

      if (entry.h) {
        return derive(code, entry.s, 'bits').then(function (raw) {
          /* The code travels with the result because the NAV manifest is
           * sealed under this same code and has to be decrypted after the
           * reveal. A hash cannot be reversed to recover it later. */
          if (b64(raw) === entry.h) return { reveal: true, code: code };
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
    if (link.parentNode.querySelector('.dr-nav-revealed')) return;

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

    link.parentNode.appendChild(list);
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
      remember(code);
      apply(result);
    }).catch(function () {
      error.hidden = false;
      input.value = '';
      input.focus();
      button.disabled = false;
      button.textContent = 'Go';
    });
  });

  /* Already hold a working code this session? Open without asking.
   *
   * Only for curtains: silently redirecting somebody who just arrived would be
   * hostile, and they did not ask to go anywhere. The field is hidden while the
   * check runs so a page the reader can already open does not flash a prompt
   * and read as broken.
   *
   * This is also what carries the revealed MENU across a folder: every page
   * under a routed index inherits the router, so each one ships its own sealed
   * manifest, and a held code re-injects the sidebar on arrival. A page OUTSIDE
   * the routed folder has no form and therefore no manifest, so the section
   * collapses again out there -- the known limit, written up in
   * docrender/visibility.py. */
  if (curtain && held().length) {
    form.style.visibility = 'hidden';

    var keys = held();
    (function tryKey(i) {
      if (i >= keys.length) {
        form.style.visibility = '';
        return;
      }
      resolve(keys[i]).then(function (result) {
        if (result.reveal) return apply(result);
        tryKey(i + 1);
      }).catch(function () {
        tryKey(i + 1);
      });
    })(0);
  }
})();
