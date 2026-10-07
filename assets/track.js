/* Jim's Burgers measurement layer.
   Nothing loads or is sent until the owner pastes IDs below. Events always go to window.dataLayer,
   so a Google Tag Manager container (gtm) can map them to GA4, Google Ads and Meta conversions. */
(() => {
  const CFG = {
    gtm: '',        // e.g. 'GTM-XXXXXXX'
    ga4: '',        // e.g. 'G-XXXXXXXXXX'
    googleAds: '',  // e.g. 'AW-1234567890'
    metaPixel: '',  // e.g. '123456789012345'
    // Google Ads conversion labels, e.g. {order: 'AbC-D_efG-h12', call: '...', directions: '...'}
    adsLabels: {}
  };
  window.dataLayer = window.dataLayer || [];
  const load = src => { const s = document.createElement('script'); s.async = true; s.src = src; document.head.appendChild(s); };
  const gtag = function () { dataLayer.push(arguments); };
  if (CFG.gtm) { dataLayer.push({'gtm.start': Date.now(), event: 'gtm.js'}); load('https://www.googletagmanager.com/gtm.js?id=' + CFG.gtm); }
  if (CFG.ga4 || CFG.googleAds) {
    window.gtag = gtag; load('https://www.googletagmanager.com/gtag/js?id=' + (CFG.ga4 || CFG.googleAds));
    gtag('js', new Date()); if (CFG.ga4) gtag('config', CFG.ga4); if (CFG.googleAds) gtag('config', CFG.googleAds);
  }
  if (CFG.metaPixel) {
    /* eslint-disable */
    !function(f,b,e,v,n,t,s){if(f.fbq)return;n=f.fbq=function(){n.callMethod?n.callMethod.apply(n,arguments):n.queue.push(arguments)};if(!f._fbq)f._fbq=n;n.push=n;n.loaded=!0;n.version='2.0';n.queue=[];t=b.createElement(e);t.async=!0;t.src=v;s=b.getElementsByTagName(e)[0];s.parentNode.insertBefore(t,s)}(window,document,'script','https://connect.facebook.net/en_US/fbevents.js');
    fbq('init', CFG.metaPixel); fbq('track', 'PageView');
  }

  // campaign context: keep utm_* and click ids for the whole visit so every event carries them
  let ctx = {};
  try {
    const q = new URLSearchParams(location.search), keep = {};
    ['utm_source', 'utm_medium', 'utm_campaign', 'utm_term', 'utm_content', 'gclid', 'fbclid'].forEach(k => q.get(k) && (keep[k] = q.get(k)));
    if (Object.keys(keep).length) sessionStorage.setItem('jb_ctx', JSON.stringify(keep));
    ctx = JSON.parse(sessionStorage.getItem('jb_ctx') || '{}');
  } catch (e) {}

  const META = {order_click: 'InitiateCheckout', call_click: 'Contact', directions_click: 'FindLocation', order_open: 'ViewContent'};
  const send = (name, p = {}) => {
    const params = Object.assign({page: location.pathname}, ctx, p);
    dataLayer.push(Object.assign({event: name}, params));
    if (window.gtag && !CFG.gtm) gtag('event', name, params);
    if (window.fbq) META[name] ? fbq('track', META[name], params) : fbq('trackCustom', name, params);
    const label = CFG.adsLabels[name.replace('_click', '')];
    if (CFG.googleAds && label && window.gtag) gtag('event', 'conversion', {send_to: CFG.googleAds + '/' + label});
  };

  const where = el => (el.closest('[id]') || {}).id || 'page';
  document.addEventListener('click', e => {
    const a = e.target.closest('a,button'); if (!a) return;
    const href = a.getAttribute('href') || '';
    if (href.startsWith('tel:')) send('call_click', {location: where(a)});
    else if (href.includes('maps/dir')) send('directions_click', {location: where(a)});
    else if (a.closest('#apps, #dlg-apps')) { let h = ''; try { h = new URL(a.href).hostname.replace('www.', ''); } catch (x) {} send('order_click', {provider: h, location: where(a)}); }
    else if (a.hasAttribute('data-order')) send('order_open', {location: where(a)});
    else if (/google\.com\/maps\/place/.test(href)) send('reviews_click', {location: where(a)});
  }, {capture: true});
  document.addEventListener('click', e => { const f = e.target.closest('[data-zoom]'); if (f) send('photo_zoom', {photo: (f.querySelector('img') || {}).src?.split('/').pop()}); });
  document.addEventListener('toggle', e => { if (e.target.matches && e.target.matches('details[open]')) send('faq_open', {question: (e.target.querySelector('summary') || {}).textContent}); }, true);

  // scroll depth with sentinels, no scroll listener
  if ('IntersectionObserver' in window && document.body.dataset.depth !== 'off') {
    const h = document.documentElement.scrollHeight;
    [25, 50, 75, 100].forEach(pct => {
      const s = document.createElement('i'); s.style.cssText = `position:absolute;left:0;width:1px;height:1px;top:${Math.min(h - 2, h * pct / 100)}px;pointer-events:none`;
      document.body.appendChild(s);
      const io = new IntersectionObserver(([en]) => { if (en.isIntersecting) { send('scroll_depth', {percent: pct}); io.disconnect(); } });
      io.observe(s);
    });
  }
  window.JBTrack = send;
})();
