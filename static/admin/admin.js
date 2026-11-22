/* AutoStock admin — mobile navigation drawer.
   Injects a sticky top bar with a hamburger that slides the sidebar in/out.
   Loaded with `defer` on every admin page. */
(function () {
  function ready(fn) {
    if (document.readyState !== 'loading') fn();
    else document.addEventListener('DOMContentLoaded', fn);
  }

  ready(function () {
    var sidebar = document.querySelector('.sidebar');
    if (!sidebar) return;

    var pageTitle = document.querySelector('.page-title');
    var label = pageTitle ? (pageTitle.textContent || '').trim() : 'Admin';

    var bar = document.createElement('header');
    bar.className = 'admin-topbar';
    bar.setAttribute('role', 'banner');

    var burger = document.createElement('button');
    burger.type = 'button';
    burger.className = 'admin-burger';
    burger.setAttribute('aria-label', 'Open menu');
    burger.setAttribute('aria-expanded', 'false');
    burger.innerHTML = '<span></span><span></span><span></span>';

    var brand = document.createElement('span');
    brand.className = 'tb-brand';
    brand.textContent = 'AutoStock';

    var title = document.createElement('span');
    title.className = 'tb-title';
    title.textContent = label;

    bar.appendChild(burger);
    bar.appendChild(brand);
    bar.appendChild(title);

    var backdrop = document.createElement('div');
    backdrop.className = 'admin-backdrop';

    document.body.insertBefore(bar, document.body.firstChild);
    document.body.appendChild(backdrop);

    function setOpen(open) {
      sidebar.classList.toggle('open', open);
      backdrop.classList.toggle('show', open);
      burger.setAttribute('aria-expanded', open ? 'true' : 'false');
      burger.setAttribute('aria-label', open ? 'Close menu' : 'Open menu');
    }

    burger.addEventListener('click', function () {
      setOpen(!sidebar.classList.contains('open'));
    });
    backdrop.addEventListener('click', function () { setOpen(false); });
    sidebar.addEventListener('click', function (e) {
      if (e.target.closest('a')) setOpen(false);
    });
    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape') setOpen(false);
    });

    // Reset the drawer state when leaving the mobile breakpoint.
    var mq = window.matchMedia('(min-width: 901px)');
    var onChange = function (e) { if (e.matches) setOpen(false); };
    if (mq.addEventListener) mq.addEventListener('change', onChange);
    else if (mq.addListener) mq.addListener(onChange);
  });

  ready(function () {
    // Wrap wide tables and add a "swipe to see more" edge cue on mobile.
    document.querySelectorAll('.table-container').forEach(function (c) {
      if (c.dataset.cueBound) return;
      c.dataset.cueBound = '1';

      var wrap = document.createElement('div');
      wrap.className = 'table-wrap';
      c.parentNode.insertBefore(wrap, c);
      wrap.appendChild(c);

      var cue = document.createElement('div');
      cue.className = 'table-cue';
      wrap.appendChild(cue);

      var sync = function () {
        var overflowing = c.scrollWidth > c.clientWidth + 4;
        var atEnd = c.scrollLeft + c.clientWidth >= c.scrollWidth - 4;
        cue.classList.toggle('visible', overflowing && !atEnd);
      };

      c.addEventListener('scroll', sync, { passive: true });
      window.addEventListener('resize', sync);
      sync();
    });
  });
})();
