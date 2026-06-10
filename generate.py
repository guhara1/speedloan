# -*- coding: utf-8 -*-
"""스피드대출 정적 사이트 생성기.

사용법:
    python3 generate.py

content_products.py / content_articles.py / content_about.py 의 데이터를 읽어
docs/ 폴더에 정적 HTML 사이트를 생성합니다. (GitHub Pages: Settings > Pages > /docs)

모든 상품 페이지는 /loan/<slug>/ 단일 URL로만 생성되며,
대상별·신청방식별·담보목적별 메뉴는 같은 URL로 링크만 연결합니다(중복 콘텐츠 방지).
"""
import html
import os
import shutil

from content_products import (PRODUCTS, TARGET_MENU, METHOD_MENU, PURPOSE_MENU,
                              CREDIT_PRODUCT_MENU, POPULAR, MEGA_GROUPS)
from content_articles import CREDIT_ARTICLES, SAFETY_ARTICLES, GUIDE_ARTICLES
from content_about import SITE_NAME, DISCLAIMER, ABOUT_PAGES

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(ROOT, "docs")

# 사이트 도메인이 정해지면 여기를 수정하세요 (sitemap.xml, canonical 태그에 사용)
BASE_URL = "https://speedloan.example.com"

P = {p["slug"]: p for p in PRODUCTS}


def esc(s):
    return html.escape(s, quote=False)


# ──────────────────────────── 내비게이션 정의 ────────────────────────────

def product_link(slug):
    return ("/loan/%s/" % slug, P[slug]["name"])


NAV = [
    {"name": "홈", "url": "/"},
    {"name": "대출상품", "url": "/loan/", "mega": [
        (g, [product_link(s) for s in slugs]) for g, slugs in MEGA_GROUPS
    ]},
    {"name": "대상별 대출", "url": "/target/", "items": [product_link(s) for s in TARGET_MENU]},
    {"name": "신청방식별 대출", "url": "/method/", "items": [product_link(s) for s in METHOD_MENU]},
    {"name": "담보·목적별 대출", "url": "/purpose/", "items": [product_link(s) for s in PURPOSE_MENU]},
    {"name": "신용·상환관리", "url": "/credit/", "items":
        [product_link(s) for s in CREDIT_PRODUCT_MENU] +
        [("/credit/%s/" % a["slug"], a["name"]) for a in CREDIT_ARTICLES]},
    {"name": "금융안전", "url": "/safety/", "items":
        [("/safety/%s/" % a["slug"], a["name"]) for a in SAFETY_ARTICLES]},
    {"name": "대출가이드", "url": "/guide/", "items":
        [("/guide/%s/" % a["slug"], a["name"]) for a in GUIDE_ARTICLES]},
    {"name": "사이트안내", "url": "/about/", "items":
        [("/about/%s/" % a["slug"] if a["slug"] else "/about/", a["name"]) for a in ABOUT_PAGES]},
]


# ──────────────────────────── HTML 조립 ────────────────────────────

def rel(prefix, url):
    """루트 기준 URL('/loan/')을 상대경로로 변환 (GitHub Pages 하위경로 호환)."""
    if url == "/":
        return prefix + "index.html" if prefix else "./"
    return prefix + url.lstrip("/")


def nav_html(prefix, current_url):
    items = []
    for menu in NAV:
        active = " active" if current_url == menu["url"] or (
            menu["url"] != "/" and current_url.startswith(menu["url"])) else ""
        if "mega" in menu:
            cols = []
            for gname, links in menu["mega"]:
                lis = "".join('<li><a href="%s">%s</a></li>' % (rel(prefix, u), esc(n)) for u, n in links)
                cols.append('<div class="mega-col"><h3>%s</h3><ul>%s</ul></div>' % (esc(gname), lis))
            items.append(
                '<li class="nav-item has-mega%s">'
                '<a href="%s">%s</a><button class="sub-toggle" aria-label="하위메뉴 열기">▾</button>'
                '<div class="mega">%s'
                '<div class="mega-all"><a href="%s">전체대출 보기 →</a></div></div></li>'
                % (active, rel(prefix, menu["url"]), esc(menu["name"]), "".join(cols), rel(prefix, "/loan/")))
        elif "items" in menu:
            lis = "".join('<li><a href="%s">%s</a></li>' % (rel(prefix, u), esc(n)) for u, n in menu["items"])
            items.append(
                '<li class="nav-item has-sub%s">'
                '<a href="%s">%s</a><button class="sub-toggle" aria-label="하위메뉴 열기">▾</button>'
                '<ul class="sub">%s</ul></li>'
                % (active, rel(prefix, menu["url"]), esc(menu["name"]), lis))
        else:
            items.append('<li class="nav-item%s"><a href="%s">%s</a></li>'
                         % (active, rel(prefix, menu["url"]), esc(menu["name"])))
    return (
        '<header class="site-header">'
        '<div class="header-inner">'
        '<a class="logo" href="%s">⚡ %s</a>'
        '<button class="nav-toggle" aria-label="메뉴 열기"><span></span><span></span><span></span></button>'
        '<nav class="main-nav"><ul class="nav-list">%s</ul></nav>'
        '</div></header>' % (rel(prefix, "/"), SITE_NAME, "".join(items)))


def footer_html(prefix):
    quick = [("/loan/", "대출상품"), ("/safety/", "금융안전"), ("/guide/", "대출가이드"),
             ("/about/", "사이트 소개"), ("/about/privacy/", "개인정보처리방침"),
             ("/about/terms/", "이용약관"), ("/about/disclaimer/", "면책고지"), ("/about/contact/", "문의하기")]
    links = " · ".join('<a href="%s">%s</a>' % (rel(prefix, u), n) for u, n in quick)
    return (
        '<footer class="site-footer">'
        '<div class="footer-inner">'
        '<div class="footer-disclaimer"><strong>안내</strong><p>%s</p></div>'
        '<p class="footer-help">대출 관련 공식 상담: 금융감독원 1332 · 서민금융진흥원 1397 · 신용회복위원회 1600-5500</p>'
        '<nav class="footer-links">%s</nav>'
        '<p class="copyright">© %s. 본 사이트의 콘텐츠를 무단 복제·전재할 수 없습니다.</p>'
        '</div></footer>' % (esc(DISCLAIMER), links, SITE_NAME))


def page(url, title, description, body, depth, h1=None, breadcrumb=None):
    prefix = "../" * depth
    crumb = ""
    if breadcrumb:
        parts = ['<a href="%s">홈</a>' % rel(prefix, "/")]
        for u, n in breadcrumb[:-1]:
            parts.append('<a href="%s">%s</a>' % (rel(prefix, u), esc(n)))
        parts.append("<span>%s</span>" % esc(breadcrumb[-1][1]))
        crumb = '<nav class="breadcrumb">%s</nav>' % " › ".join(parts)
    full_title = title if title == SITE_NAME else "%s | %s" % (title, SITE_NAME)
    return """<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>%s</title>
<meta name="description" content="%s">
<link rel="canonical" href="%s">
<link rel="stylesheet" href="%sassets/style.css">
</head>
<body>
%s
<main class="container">
%s%s
</main>
%s
<script src="%sassets/script.js"></script>
</body>
</html>
""" % (esc(full_title), esc(description), BASE_URL + url, prefix,
       nav_html(prefix, url),
       crumb, body,
       footer_html(prefix), prefix)


def render_body_item(item):
    if isinstance(item, list):
        return "<ul>%s</ul>" % "".join("<li>%s</li>" % esc(li) for li in item)
    return "<p>%s</p>" % esc(item)


def render_sections(sections):
    out = []
    for sec in sections:
        out.append("<section><h2>%s</h2>%s</section>"
                   % (esc(sec["h"]), "".join(render_body_item(b) for b in sec["body"])))
    return "".join(out)


def render_faq(faq):
    if not faq:
        return ""
    qa = "".join("<details><summary>%s</summary><p>%s</p></details>" % (esc(q), esc(a)) for q, a in faq)
    return '<section class="faq"><h2>자주 묻는 질문</h2>%s</section>' % qa


def related_cards(prefix, slugs):
    if not slugs:
        return ""
    cards = "".join(
        '<a class="card" href="%s"><h3>%s</h3><p>%s</p></a>'
        % (rel(prefix, "/loan/%s/" % s), esc(P[s]["name"]), esc(P[s]["summary"][:58] + "…"))
        for s in slugs if s in P)
    return '<section class="related"><h2>함께 보면 좋은 글</h2><div class="card-grid">%s</div></section>' % cards


def article_disclaimer():
    return ('<div class="notice"><p>%s</p></div>' % esc(DISCLAIMER))


def write(path, content):
    full = os.path.join(OUT, path.lstrip("/"))
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w", encoding="utf-8") as f:
        f.write(content)


# ──────────────────────────── 페이지 생성 ────────────────────────────

URLS = []  # sitemap용


def emit(url, title, description, body, h1=None, breadcrumb=None):
    depth = url.count("/") - 1
    write(url + "index.html", page(url, title, description, body, depth, h1, breadcrumb))
    URLS.append(url)


def product_page(p):
    url = "/loan/%s/" % p["slug"]
    prefix = "../" * 2
    body = '<article><h1>%s</h1><p class="lead">%s</p>%s%s%s%s</article>' % (
        esc(p["name"]), esc(p["summary"]),
        render_sections(p["sections"]),
        render_faq(p.get("faq")),
        related_cards(prefix, p.get("related", [])),
        article_disclaimer())
    emit(url, p["name"] + " 조건과 주의사항", p["summary"], body,
         breadcrumb=[("/loan/", "대출상품"), (url, p["name"])])


def article_page(base, label, a):
    url = "/%s/%s/" % (base, a["slug"])
    prefix = "../" * 2
    body = '<article><h1>%s</h1><p class="lead">%s</p>%s%s%s</article>' % (
        esc(a["name"]), esc(a["summary"]),
        render_sections(a["sections"]),
        related_cards(prefix, a.get("related_products", [])),
        article_disclaimer())
    emit(url, a["name"], a["summary"], body,
         breadcrumb=[("/%s/" % base, label), (url, a["name"])])


def listing_page(url, title, intro, entries, extra=""):
    prefix = "../" * (url.count("/") - 1)
    cards = "".join('<a class="card" href="%s"><h3>%s</h3><p>%s</p></a>'
                    % (rel(prefix, u), esc(n), esc(d)) for u, n, d in entries)
    body = '<h1>%s</h1><p class="lead">%s</p><div class="card-grid">%s</div>%s%s' % (
        esc(title), esc(intro), cards, extra, article_disclaimer())
    emit(url, title, intro, body, breadcrumb=[(url, title)])


def home_page():
    prefix = ""
    def cards(slugs):
        return "".join('<a class="card" href="%s"><h3>%s</h3><p>%s</p></a>'
                       % (rel(prefix, "/loan/%s/" % s), esc(P[s]["name"]), esc(P[s]["summary"][:60] + "…"))
                       for s in slugs)
    def chips(slugs):
        return "".join('<a class="chip" href="%s">%s</a>'
                       % (rel(prefix, "/loan/%s/" % s), esc(P[s]["name"])) for s in slugs)

    guides = GUIDE_ARTICLES[:4]
    guide_cards = "".join('<a class="card" href="%s"><h3>%s</h3><p>%s</p></a>'
                          % (rel(prefix, "/guide/%s/" % g["slug"]), esc(g["name"]), esc(g["summary"][:60] + "…"))
                          for g in guides)
    check_items = [
        ("월 상환액은 실수령액의 30% 이내인가요?", "/credit/repayment-plan/"),
        ("정책 서민금융 상품 대상인지 확인했나요?", "/loan/low-credit-loan/"),
        ("거래 상대가 등록 금융회사인지 조회했나요?", "/safety/illegal-loan/"),
        ("선입금·수수료 요구는 없나요? (있다면 사기)", "/safety/loan-fraud/"),
    ]
    checks = "".join('<li><a href="%s">%s</a></li>' % (rel(prefix, u), esc(t)) for t, u in check_items)
    faq = [
        ("대출 조회만 해도 신용점수가 떨어지나요?",
         "한도·조건 조회는 신용점수에 영향을 주지 않습니다. 실제 신청·실행 기록만 신용평가에 반영되므로, 비교는 충분히 하고 신청은 신중하게 하세요."),
        ("무직자도 대출이 가능한가요?",
         "일반 신용대출은 어렵지만 비상금대출, 예·적금/보험 담보대출, 정책 서민금융 등 검토할 수 있는 선택지가 있습니다. 무직자대출 페이지에서 자세히 안내합니다."),
        ("'무조건 승인' 광고는 믿어도 되나요?",
         "제도권 금융에 심사 없는 대출은 존재하지 않습니다. 이런 광고는 불법 사금융이므로 절대 연락하지 마시고, 금융안전 메뉴의 구별법을 확인하세요."),
        ("이 사이트에서 대출을 신청할 수 있나요?",
         "아니요. 본 사이트는 대출을 제공·중개하지 않는 정보 사이트입니다. 실제 신청은 각 금융회사의 공식 채널을 이용하시기 바랍니다."),
    ]
    faq_html = "".join("<details><summary>%s</summary><p>%s</p></details>" % (esc(q), esc(a)) for q, a in faq)

    body = """
<section class="hero">
<h1>대출, 알아보고 결정하세요</h1>
<p>%s은 대출상품의 조건·필요서류·주의사항을 쉽게 풀어 안내하는 대출 정보 사이트입니다.<br>
대출을 제공하거나 중개하지 않으며, 과장 없는 정보만 전합니다.</p>
<div class="hero-links">
<a class="btn" href="%s">대출상품 전체보기</a>
<a class="btn btn-outline" href="%s">대출 전 체크리스트</a>
</div>
</section>

<section><h2>자주 찾는 대출상품</h2><div class="card-grid">%s</div></section>

<section><h2>대상별 대출 바로가기</h2><div class="chip-row">%s</div></section>

<section><h2>신청방식별 대출 바로가기</h2><div class="chip-row">%s</div></section>

<section class="check-section"><h2>대출 전 확인사항</h2>
<p>대출 신청 버튼을 누르기 전에 아래 네 가지만은 꼭 확인하세요.</p>
<ul class="check-list">%s</ul>
<p><a href="%s">→ 전체 체크리스트 보기</a></p>
</section>

<section><h2>최신 대출가이드</h2><div class="card-grid">%s</div>
<p><a href="%s">→ 대출가이드 전체보기</a></p></section>

<section class="faq"><h2>자주 묻는 질문</h2>%s</section>
%s""" % (
        SITE_NAME,
        rel(prefix, "/loan/"), rel(prefix, "/safety/checklist/"),
        cards(POPULAR[:6]),
        chips(TARGET_MENU),
        chips(METHOD_MENU),
        checks, rel(prefix, "/safety/checklist/"),
        guide_cards, rel(prefix, "/guide/"),
        faq_html,
        article_disclaimer())
    write("/index.html", page("/", SITE_NAME,
        "대출상품의 조건, 필요서류, 주의사항을 쉽게 안내하는 대출 정보 사이트. 무직자대출, 직장인대출, 비상금대출, 소액대출, 저신용자대출 정보를 과장 없이 정리했습니다.",
        body, 0))
    URLS.append("/")


def build():
    if os.path.exists(OUT):
        shutil.rmtree(OUT)
    os.makedirs(OUT)

    # 정적 자원
    for asset in ("style.css", "script.js"):
        shutil.copy(os.path.join(ROOT, "assets", asset), ensure_assets_dir(asset))

    home_page()

    # 상품 페이지 (단일 URL)
    for p in PRODUCTS:
        product_page(p)

    # 대출상품 전체 목록
    listing_page("/loan/", "대출상품 전체보기",
                 "스피드대출에서 다루는 모든 대출상품입니다. 각 페이지에서 일반적인 조건, 필요서류, 주의사항을 확인할 수 있습니다.",
                 [("/loan/%s/" % p["slug"], p["name"], p["summary"][:60] + "…") for p in PRODUCTS])

    # 분류별 목록 (같은 상품 URL로 링크만 연결)
    listing_page("/target/", "대상별 대출",
                 "직장인, 무직자, 주부, 프리랜서, 자영업자 등 내 상황에 맞는 대출 정보를 찾아보세요.",
                 [("/loan/%s/" % s, P[s]["name"], P[s]["summary"][:60] + "…") for s in TARGET_MENU])
    listing_page("/method/", "신청방식별 대출",
                 "모바일, 온라인, 비대면, 무방문, 당일 — 신청 방법에 따라 달라지는 절차와 주의사항을 안내합니다.",
                 [("/loan/%s/" % s, P[s]["name"], P[s]["summary"][:60] + "…") for s in METHOD_MENU])
    listing_page("/purpose/", "담보·목적별 대출",
                 "자동차, 부동산, 생활비, 비상금 등 담보와 목적이 분명한 대출 정보를 모았습니다.",
                 [("/loan/%s/" % s, P[s]["name"], P[s]["summary"][:60] + "…") for s in PURPOSE_MENU])

    # 신용·상환관리
    listing_page("/credit/", "신용·상환관리",
                 "신용점수 관리부터 상환계획, 금리 비교, 연체 대응까지 — 대출을 건강하게 관리하는 방법을 안내합니다.",
                 [("/loan/%s/" % s, P[s]["name"], P[s]["summary"][:60] + "…") for s in CREDIT_PRODUCT_MENU] +
                 [("/credit/%s/" % a["slug"], a["name"], a["summary"][:60] + "…") for a in CREDIT_ARTICLES])
    for a in CREDIT_ARTICLES:
        article_page("credit", "신용·상환관리", a)

    # 금융안전
    listing_page("/safety/", "금융안전",
                 "불법 사금융과 대출 사기로부터 나를 지키는 방법입니다. 대출을 알아보기 전에 꼭 한 번 읽어보세요.",
                 [("/safety/%s/" % a["slug"], a["name"], a["summary"][:60] + "…") for a in SAFETY_ARTICLES])
    for a in SAFETY_ARTICLES:
        article_page("safety", "금융안전", a)

    # 대출가이드
    listing_page("/guide/", "대출가이드",
                 "대출 기초상식부터 한도·금리의 원리, 필요서류, 거절 이유까지 — 대출을 처음 알아보는 분을 위한 가이드입니다.",
                 [("/guide/%s/" % a["slug"], a["name"], a["summary"][:60] + "…") for a in GUIDE_ARTICLES])
    for a in GUIDE_ARTICLES:
        article_page("guide", "대출가이드", a)

    # 사이트안내
    intro_about = ABOUT_PAGES[0]
    about_extra = '<article>%s</article>' % render_sections(intro_about["sections"])
    listing_page("/about/", "사이트안내",
                 intro_about["summary"],
                 [("/about/%s/" % a["slug"], a["name"], a["summary"]) for a in ABOUT_PAGES if a["slug"]],
                 extra=about_extra)
    for a in ABOUT_PAGES:
        if a["slug"]:
            article_page("about", "사이트안내", a)

    # sitemap.xml / robots.txt
    sm = ['<?xml version="1.0" encoding="UTF-8"?>',
          '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for u in sorted(set(URLS)):
        sm.append("<url><loc>%s%s</loc></url>" % (BASE_URL, u))
    sm.append("</urlset>")
    write("/sitemap.xml", "\n".join(sm) + "\n")
    write("/robots.txt", "User-agent: *\nAllow: /\nSitemap: %s/sitemap.xml\n" % BASE_URL)

    print("생성 완료: %d개 페이지 → docs/" % len(set(URLS)))


def ensure_assets_dir(asset):
    d = os.path.join(OUT, "assets")
    os.makedirs(d, exist_ok=True)
    return os.path.join(d, asset)


if __name__ == "__main__":
    build()
