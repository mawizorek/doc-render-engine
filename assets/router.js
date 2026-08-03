/* Client half of the router. Server half is docrender/router.py.
 *
 * THESE TWO FILES SHARE THE CIPHER, THE KDF AND THE ITERATION COUNT.
 * Change one without the other and every router silently stops working, with
 * no error a reader could act on. They move in the same PR, always.
 *
 * WHAT IT DOES. Derives a key from what was typed, tries it against each
 * wrapped destination until one decrypts, then navigates there. A wrong code
 * decrypts nothing -- it fails to DECRYPT rather than failing a comparison --
 * so there is no plaintext destination in the page to read around.
 *
 * The wraps are unlabelled and shuffled at build time, so trying them in order
 * leaks nothing about which is which.
 *
 * NOT A SECURITY BOUNDARY, said here where somebody reading the crypto will
 * see it: the site is public and every destination is reachable by URL. This
 * keeps a casual reader out of the way and lets one code drop one person
 * somewhere specific. Full reasoning in docrender/router.py.
 */

(function () {
  var form = document.querySelector('.dr-router');
  if (!form || !window.crypto || !crypto.subtle) return;

  var input = form.querySelector('.dr-router__input');
  var button = form.querySelector('.dr-router__btn');
  var error = form.querySelector('.dr-router__error');

  function bytes(s) {
    return Uint8Array.from(atob(s), function (c) { return c.charCodeAt(0); });
  }

  function routes() {
    try {
      return JSON.parse(atob(form.dataset.routes)) || [];
    } catch (e) {
      return [];
    }
  }

  function derive(code, salt) {
    return crypto.subtle.importKey(
      'raw', new TextEncoder().encode(code), 'PBKDF2', false, ['deriveKey']
    ).then(function (material) {
      return crypto.subtle.deriveKey(
        { name: 'PBKDF2',
          salt: bytes(salt),
          iterations: parseInt(form.dataset.iter, 10),
          hash: 'SHA-256' },
        material,
        { name: 'AES-GCM', length: 256 },
        false,
        ['decrypt']
      );
    });
  }

  /* One code against every wrap, sequentially. The common case is a handful
   * of routes, and firing every PBKDF2 at once would burn a phone's battery
   * to save nothing measurable. */
  function resolve(code) {
    var all = routes();

    function attempt(i) {
      if (i >= all.length) return Promise.reject(new Error('no route'));
      var entry = all[i];
      return derive(code, entry.s).then(function (key) {
        return crypto.subtle.decrypt(
          { name: 'AES-GCM', iv: bytes(entry.n) }, key, bytes(entry.w)
        );
      }).then(function (plain) {
        return new TextDecoder().decode(plain);
      }).catch(function () {
        return attempt(i + 1);
      });
    }

    return attempt(0);
  }

  form.addEventListener('submit', function (e) {
    e.preventDefault();
    var code = input.value.trim();
    if (!code) return;

    error.hidden = true;
    button.disabled = true;
    button.textContent = 'Checking';

    resolve(code).then(function (destination) {
      window.location.href = destination;
    }).catch(function () {
      error.hidden = false;
      input.value = '';
      input.focus();
      button.disabled = false;
      button.textContent = 'Go';
    });
  });
})();
