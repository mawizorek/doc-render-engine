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

  function routes() {
    try {
      return JSON.parse(atob(form.dataset.routes)) || [];
    } catch (e) {
      return [];
    }
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
          if (b64(raw) === entry.h) return { reveal: true };
          return next();
        }).catch(next);
      }

      return derive(code, entry.s).then(function (key) {
        return crypto.subtle.decrypt(
          { name: 'AES-GCM', iv: bytes(entry.n) }, key, bytes(entry.w)
        );
      }).then(function (plain) {
        return { go: new TextDecoder().decode(plain) };
      }).catch(next);
    }

    return attempt(0);
  }

  function apply(result) {
    if (result.go) {
      window.location.href = result.go;
      return;
    }
    if (curtain) {
      curtain.hidden = false;
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
   * and read as broken. */
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
