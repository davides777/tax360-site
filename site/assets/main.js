/* TAX360 — shared behaviour */
(function(){
  const header = document.getElementById('header');
  const logoImg = document.getElementById('logoImg');
  // Asset folder resolved from this script's own URL, so pages in sub-folders (news/…) work too
  const ASSETS = (document.currentScript && document.currentScript.src)
    ? document.currentScript.src.replace(/main\.js(\?.*)?$/, '') : 'assets/';
  const LOGO_DARK = ASSETS + 'logo-dark.png';   // white letters → for dark hero
  const LOGO_LIGHT = ASSETS + 'logo-light.png'; // navy letters  → for white header

  // Pages with a dark hero use transparent header at top; "solid" pages always have white header.
  const isSolid = header && header.classList.contains('solid');

  function applyHeader(){
    if(isSolid) return; // stays solid; logo handled below
    const scrolled = window.scrollY > 60;
    header.classList.toggle('scrolled', scrolled);
    if(logoImg) logoImg.src = scrolled ? LOGO_LIGHT : LOGO_DARK;
  }
  if(header && !isSolid){
    applyHeader();
    window.addEventListener('scroll', applyHeader, {passive:true});
  }
  if(isSolid && logoImg){ logoImg.src = LOGO_LIGHT; }

  // Slide-out menu
  const menuToggle = document.getElementById('menuToggle');
  const menuClose  = document.getElementById('menuClose');
  const menuOverlay= document.getElementById('menuOverlay');
  function openMenu(){document.body.classList.add('menu-open');}
  function closeMenu(){document.body.classList.remove('menu-open');}
  if(menuToggle) menuToggle.addEventListener('click',()=>{document.body.classList.contains('menu-open')?closeMenu():openMenu();});
  if(menuClose) menuClose.addEventListener('click',closeMenu);
  if(menuOverlay) menuOverlay.addEventListener('click',closeMenu);
  document.querySelectorAll('[data-close]').forEach(a=>a.addEventListener('click',closeMenu));
  document.addEventListener('keydown',e=>{if(e.key==='Escape')closeMenu();});

  // Partner photos: no right-click / drag-to-save
  document.querySelectorAll('.no-save').forEach(function(el){
    el.addEventListener('contextmenu',function(e){e.preventDefault();});
    el.addEventListener('dragstart',function(e){e.preventDefault();});
  });

  // Reveal on scroll
  const io=new IntersectionObserver((entries)=>{
    entries.forEach(e=>{if(e.isIntersecting){e.target.classList.add('in');io.unobserve(e.target)}})
  },{threshold:.15});
  document.querySelectorAll('.reveal-on-scroll').forEach(el=>io.observe(el));
})();
