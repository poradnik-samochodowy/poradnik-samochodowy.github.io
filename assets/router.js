(function () {
  'use strict';

  // Record initial URL so popstate works on first back
  history.replaceState({ path: location.pathname }, '', location.pathname);

  // Intercept all same-origin link clicks
  document.addEventListener('click', function (e) {
    var a = e.target.closest('a');
    if (!a) return;
    var href = a.getAttribute('href');
    if (!href) return;
    // Skip: external, anchors, new-tab, downloads
    if (a.target === '_blank' || a.hasAttribute('download')) return;
    if (href.startsWith('http') || href.startsWith('//') ||
        href.startsWith('#') || href.startsWith('mailto:') ||
        href.startsWith('tel:')) return;
    e.preventDefault();
    navigate(href);
  });

  // Browser back / forward
  window.addEventListener('popstate', function () {
    load(location.pathname, false);
  });

  function navigate(path) {
    if (path === location.pathname) return;
    history.pushState({ path: path }, '', path);
    load(path, true);
  }

  function load(path, doScroll) {
    // Normalize: /foo → /foo/index.html if no extension, but fetch as-is
    document.body.classList.add('ps-nav-loading');

    fetch(path)
      .then(function (r) {
        if (!r.ok) throw new Error(r.status);
        return r.text();
      })
      .then(function (html) {
        var doc = new DOMParser().parseFromString(html, 'text/html');

        // Swap page metadata
        document.title = doc.title;
        swapMeta(doc, 'name', 'description');
        swapMeta(doc, 'name', 'robots');
        var canonical = doc.querySelector('link[rel="canonical"]');
        var curCanon  = document.querySelector('link[rel="canonical"]');
        if (canonical && curCanon) curCanon.href = canonical.href;

        // Identify content region in both old and new doc
        var newNodes = getContentNodes(doc.body);
        if (!newNodes.length) { location.href = path; return; }

        var topbar = document.querySelector('header.topbar');
        var footer  = document.querySelector('footer');
        if (!topbar || !footer) { location.href = path; return; }

        // Remove existing between-header-and-footer nodes
        var cur = topbar.nextSibling;
        while (cur && cur !== footer) {
          var nxt = cur.nextSibling;
          cur.remove();
          cur = nxt;
        }

        // Insert fetched content nodes before footer
        var frag = document.createDocumentFragment();
        newNodes.forEach(function (n) {
          frag.appendChild(document.importNode(n, true));
        });
        document.body.insertBefore(frag, footer);

        document.body.classList.remove('ps-nav-loading');
        if (doScroll) window.scrollTo({ top: 0, behavior: 'instant' });
      })
      .catch(function () {
        document.body.classList.remove('ps-nav-loading');
        location.href = path;
      });
  }

  function getContentNodes(body) {
    var kids = Array.from(body.children);
    var hIdx = kids.findIndex(function (el) {
      return el.tagName === 'HEADER' && el.classList.contains('topbar');
    });
    var fIdx = kids.findIndex(function (el) { return el.tagName === 'FOOTER'; });
    var start = hIdx >= 0 ? hIdx + 1 : 0;
    var end   = fIdx >= 0 ? fIdx : kids.length;
    return kids.slice(start, end);
  }

  function swapMeta(doc, attr, val) {
    var n = doc.querySelector('meta[' + attr + '="' + val + '"]');
    var c = document.querySelector('meta[' + attr + '="' + val + '"]');
    if (n && c) c.setAttribute('content', n.getAttribute('content'));
  }
})();
