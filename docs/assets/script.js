// 모바일 내비게이션 토글
(function () {
  var toggle = document.querySelector('.nav-toggle');
  var nav = document.querySelector('.main-nav');
  if (toggle && nav) {
    toggle.addEventListener('click', function () {
      nav.classList.toggle('open');
    });
  }
  // 모바일에서 하위메뉴 펼치기
  document.querySelectorAll('.sub-toggle').forEach(function (btn) {
    btn.addEventListener('click', function (e) {
      e.preventDefault();
      var item = btn.closest('.nav-item');
      var wasOpen = item.classList.contains('open');
      document.querySelectorAll('.nav-item.open').forEach(function (it) {
        it.classList.remove('open');
      });
      if (!wasOpen) item.classList.add('open');
    });
  });
})();

// 좌측 목차(TOC) 스크롤스파이 — 현재 읽는 섹션을 골드로 표시
(function () {
  var links = document.querySelectorAll('.toc a[href^="#"]');
  if (!links.length || !('IntersectionObserver' in window)) return;

  var map = {};
  var targets = [];
  links.forEach(function (a) {
    var id = a.getAttribute('href').slice(1);
    var el = document.getElementById(id);
    if (el) { map[id] = a; targets.push(el); }
  });
  if (!targets.length) return;

  function activate(id) {
    links.forEach(function (a) { a.classList.remove('active'); });
    if (map[id]) map[id].classList.add('active');
  }

  var visible = {};
  var observer = new IntersectionObserver(function (entries) {
    entries.forEach(function (e) { visible[e.target.id] = e.isIntersecting; });
    for (var i = 0; i < targets.length; i++) {
      if (visible[targets[i].id]) { activate(targets[i].id); return; }
    }
  }, { rootMargin: '-80px 0px -55% 0px', threshold: 0 });

  targets.forEach(function (el) { observer.observe(el); });

  // 목차 클릭 시 즉시 표시
  links.forEach(function (a) {
    a.addEventListener('click', function () {
      activate(a.getAttribute('href').slice(1));
    });
  });
})();
