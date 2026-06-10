# -*- coding: utf-8 -*-
"""스피드대출 정적 사이트 생성기.

사용법:
    python3 generate.py

content_products.py / content_articles.py / content_about.py 의 데이터를 읽어
docs/ 폴더와 저장소 루트에 정적 HTML 사이트를 생성합니다.

모든 상품 페이지는 /loan/<slug>/ 단일 URL로만 생성되며,
대상별·신청방식별·담보목적별 메뉴는 같은 URL로 링크만 연결합니다(중복 콘텐츠 방지).

디자인: 다크 럭스 스파 — 다크 네이비 배경, 골드 강조, 좌측 고정 목차(TOC).
"""
import html
import json
import os
import shutil

from content_products import (PRODUCTS, TARGET_MENU, METHOD_MENU, PURPOSE_MENU,
                              CREDIT_PRODUCT_MENU, POPULAR, MEGA_GROUPS)
from content_articles import CREDIT_ARTICLES, SAFETY_ARTICLES, GUIDE_ARTICLES
from content_about import SITE_NAME, DISCLAIMER, ABOUT_PAGES

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(ROOT, "docs")

# 사이트 도메인이 정해지면 여기를 수정하세요 (sitemap.xml, canonical 태그에 사용)
BASE_URL = "https://speedloan.pages.dev"

# 콘텐츠 정보 기준일 — 내용을 갱신할 때마다 함께 갱신하세요
BASELINE_DATE = "2026년 6월"

# 대표 썸네일 (make_og.py로 생성)
OG_IMAGE = BASE_URL + "/assets/og-image.png"

# ──────────────────────────── 애드센스 설정 ────────────────────────────
# 애드센스 승인 후 발급받은 게시자 ID를 입력하고 python3 generate.py 로 재빌드하면
# 아래 정의된 위치에 광고가 활성화됩니다. 비워두면 광고 코드가 전혀 출력되지 않습니다.
#   예: ADSENSE_CLIENT = "ca-pub-1234567890123456"
ADSENSE_CLIENT = ""

# 애드센스에서 '디스플레이 광고' 단위를 만들고 위치별 슬롯 ID를 넣으세요.
# 슬롯 ID를 비워두면 해당 위치는 자동 형식(data-ad-format=auto)으로만 출력됩니다.
ADSENSE_SLOTS = {
    "home_top": "",        # 홈: 히어로 설명문 아래, 대출상품 카드 위
    "home_middle": "",     # 홈: 신청방식별 대출 비교 아래
    "home_bottom": "",     # 홈: 최신 대출가이드 아래
    "article_top": "",     # 글: 제목·바이라인 아래, 본문 시작 전
    "article_middle": "",  # 글: 본문 중간 (섹션 4개 이상인 긴 글에만)
    "article_bottom": "",  # 글: 본문 끝, 면책 안내 위
    "list_bottom": "",     # 목록 페이지: 카드 그리드 아래
}


def ad_slot(name):
    """광고 슬롯. ADSENSE_CLIENT가 비어 있으면 아무것도 출력하지 않는다.

    - '광고' 라벨로 콘텐츠와 명확히 구분 (메뉴/본문처럼 보이는 배치 금지 정책 준수)
    - min-height는 CSS에서 예약해 광고 로딩 시 화면 밀림(CLS) 방지
    """
    if not ADSENSE_CLIENT:
        return ""
    slot = ADSENSE_SLOTS.get(name, "")
    slot_attr = ' data-ad-slot="%s"' % slot if slot else ""
    return ('<div class="ad-slot"><span class="ad-label">광고</span>'
            '<ins class="adsbygoogle" style="display:block" data-ad-client="%s"%s'
            ' data-ad-format="auto" data-full-width-responsive="true"></ins>'
            '<script>(adsbygoogle=window.adsbygoogle||[]).push({});</script>'
            '</div>' % (ADSENSE_CLIENT, slot_attr))


def adsense_head():
    if not ADSENSE_CLIENT:
        return ""
    return ('<script async src="https://pagead2.googlesyndication.com/pagead/js/'
            'adsbygoogle.js?client=%s" crossorigin="anonymous"></script>\n' % ADSENSE_CLIENT)

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
    """루트 기준 URL('/loan/')을 상대경로로 변환."""
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
        '<a class="logo" href="%s"><span class="logo-mark">✦</span> %s</a>'
        '<button class="nav-toggle" aria-label="메뉴 열기"><span></span><span></span><span></span></button>'
        '<nav class="main-nav"><ul class="nav-list">%s</ul></nav>'
        '</div></header>' % (rel(prefix, "/"), SITE_NAME, "".join(items)))


def footer_html(prefix):
    quick = [("/about/", "사이트 소개"), ("/about/author/", "작성자 소개"),
             ("/about/editorial/", "콘텐츠 작성 기준"), ("/about/contact/", "문의하기"),
             ("/about/privacy/", "개인정보처리방침"), ("/about/terms/", "이용약관"),
             ("/about/disclaimer/", "면책고지"), ("/about/ads/", "광고·제휴 안내")]
    links = " · ".join('<a href="%s">%s</a>' % (rel(prefix, u), n) for u, n in quick)
    return (
        '<footer class="site-footer">'
        '<div class="footer-inner">'
        '<div class="footer-disclaimer"><strong>안내</strong><p>%s</p></div>'
        '<p class="footer-help">대출 관련 공식 상담: 금융감독원 1332 · 서민금융진흥원 1397 · 신용회복위원회 1600-5500</p>'
        '<nav class="footer-links">%s</nav>'
        '<p class="copyright">© %s. 본 사이트의 콘텐츠를 무단 복제·전재할 수 없습니다.</p>'
        '</div></footer>' % (esc(DISCLAIMER), links, SITE_NAME))


def page(url, title, description, body, depth, breadcrumb=None, head_extra="", wide=False):
    prefix = "../" * depth
    crumb = ""
    if breadcrumb:
        parts = ['<a href="%s">홈</a>' % rel(prefix, "/")]
        for u, n in breadcrumb[:-1]:
            parts.append('<a href="%s">%s</a>' % (rel(prefix, u), esc(n)))
        parts.append("<span>%s</span>" % esc(breadcrumb[-1][1]))
        crumb = '<nav class="breadcrumb">%s</nav>' % " › ".join(parts)
    full_title = title if title == SITE_NAME else "%s | %s" % (title, SITE_NAME)
    container = "container wide" if wide else "container"
    return ("""<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>%s</title>
<meta name="description" content="%s">
<link rel="canonical" href="%s">
<meta property="og:type" content="website">
<meta property="og:title" content="%s">
<meta property="og:description" content="%s">
<meta property="og:url" content="%s">
<meta property="og:image" content="{og}">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:image:alt" content="대출상품 조건과 신용관리 정보를 정리한 생활금융 가이드">
<meta name="twitter:card" content="summary_large_image">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Noto+Serif+KR:wght@600;700&display=swap" rel="stylesheet">
<link rel="stylesheet" href="%sassets/style.css">
%s</head>
<body>
%s
<main class="%s">
%s%s
</main>
%s
<script src="%sassets/script.js"></script>
</body>
</html>
""" % (esc(full_title), esc(description), BASE_URL + url,
       esc(full_title), esc(description), BASE_URL + url, prefix,
       adsense_head() + head_extra,
       nav_html(prefix, url),
       container,
       crumb, body,
       footer_html(prefix), prefix)).replace("{og}", OG_IMAGE)


def render_body_item(item):
    if isinstance(item, list):
        return "<ul>%s</ul>" % "".join("<li>%s</li>" % esc(li) for li in item)
    return "<p>%s</p>" % esc(item)


def render_sections(sections):
    """본문 섹션 렌더링. 좌측 목차(TOC)용 앵커 id를 부여한다."""
    out = []
    for i, sec in enumerate(sections, 1):
        out.append('<section id="sec-%d"><h2>%s</h2>%s</section>'
                   % (i, esc(sec["h"]), "".join(render_body_item(b) for b in sec["body"])))
    return "".join(out)


def toc_aside(items):
    """좌측 고정 목차. items = [(anchor, label), ...]"""
    lis = "".join('<li><a href="%s">%s</a></li>' % (a, esc(n)) for a, n in items)
    return ('<aside class="toc" aria-label="목차"><div class="toc-inner">'
            '<p class="toc-title">목차</p><nav><ol>%s</ol></nav>'
            '</div></aside>' % lis)


def toc_items_for(sections, has_faq=False, has_related=False):
    items = [("#sec-%d" % i, sec["h"]) for i, sec in enumerate(sections, 1)]
    if has_faq:
        items.append(("#faq", "자주 묻는 질문"))
    if has_related:
        items.append(("#related", "함께 보면 좋은 글"))
    return items


def render_faq(faq, title="자주 묻는 질문"):
    if not faq:
        return ""
    qa = "".join("<details><summary>%s</summary><p>%s</p></details>" % (esc(q), esc(a)) for q, a in faq)
    return '<section class="faq" id="faq"><h2>%s</h2>%s</section>' % (esc(title), qa)


def byline():
    return ('<p class="byline">작성·검수: %s 운영자 · 정보 기준일: %s · '
            '<span>제도 변경 시 내용이 업데이트될 수 있습니다.</span></p>'
            % (SITE_NAME, BASELINE_DATE))


def related_cards(prefix, slugs):
    if not slugs:
        return ""
    cards = "".join(
        '<a class="card" href="%s"><h3>%s</h3><p>%s</p></a>'
        % (rel(prefix, "/loan/%s/" % s), esc(P[s]["name"]), esc(P[s]["summary"][:58] + "…"))
        for s in slugs if s in P)
    return ('<section class="related" id="related"><h2>함께 보면 좋은 글</h2>'
            '<div class="card-grid">%s</div></section>' % cards)


def article_disclaimer():
    return ('<div class="notice"><p>%s</p></div>' % esc(DISCLAIMER))


def write(path, content):
    full = os.path.join(OUT, path.lstrip("/"))
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w", encoding="utf-8") as f:
        f.write(content)


# ──────────────────────────── 페이지 생성 ────────────────────────────

URLS = []  # sitemap용


def emit(url, title, description, body, breadcrumb=None, head_extra="", wide=False):
    depth = url.count("/") - 1
    write(url + "index.html", page(url, title, description, body, depth, breadcrumb, head_extra, wide))
    URLS.append(url)


def sections_with_mid_ad(sections):
    """본문 섹션 렌더링 + 긴 글(섹션 4개 이상)은 2번째 섹션 뒤에 중간 광고 삽입."""
    html_out = render_sections(sections)
    if len(sections) >= 4:
        marker = '<section id="sec-3">'
        html_out = html_out.replace(marker, ad_slot("article_middle") + marker, 1)
    return html_out


def product_page(p):
    url = "/loan/%s/" % p["slug"]
    prefix = "../" * 2
    toc = toc_aside(toc_items_for(p["sections"], has_faq=bool(p.get("faq")),
                                  has_related=bool(p.get("related"))))
    body = ('<div class="page-grid">%s'
            '<article><h1>%s</h1><p class="lead">%s</p>%s%s%s%s%s%s%s</article></div>') % (
        toc,
        esc(p["name"]), esc(p["summary"]),
        byline(),
        ad_slot("article_top"),
        sections_with_mid_ad(p["sections"]),
        render_faq(p.get("faq")),
        related_cards(prefix, p.get("related", [])),
        ad_slot("article_bottom"),
        article_disclaimer())
    emit(url, p["name"] + " 조건과 주의사항", p["summary"], body,
         breadcrumb=[("/loan/", "대출상품"), (url, p["name"])], wide=True)


def article_page(base, label, a):
    url = "/%s/%s/" % (base, a["slug"])
    prefix = "../" * 2
    related = a.get("related_products", [])
    toc = toc_aside(toc_items_for(a["sections"], has_related=bool(related)))
    body = ('<div class="page-grid">%s'
            '<article><h1>%s</h1><p class="lead">%s</p>%s%s%s%s%s%s</article></div>') % (
        toc,
        esc(a["name"]), esc(a["summary"]),
        byline(),
        ad_slot("article_top"),
        sections_with_mid_ad(a["sections"]),
        related_cards(prefix, related),
        ad_slot("article_bottom"),
        article_disclaimer())
    emit(url, a["name"], a["summary"], body,
         breadcrumb=[("/%s/" % base, label), (url, a["name"])], wide=True)


def listing_page(url, title, intro, entries, extra=""):
    prefix = "../" * (url.count("/") - 1)
    cards = "".join('<a class="card" href="%s"><h3>%s</h3><p>%s</p></a>'
                    % (rel(prefix, u), esc(n), esc(d)) for u, n, d in entries)
    body = '<h1>%s</h1><p class="lead">%s</p><div class="card-grid">%s</div>%s%s%s' % (
        esc(title), esc(intro), cards, extra, ad_slot("list_bottom"), article_disclaimer())
    emit(url, title, intro, body, breadcrumb=[(url, title)])


# ──────────────────────────── 메인페이지 ────────────────────────────

HOME_H1 = "대출상품 조건과 신용관리 정보를 쉽게 정리한 생활금융 가이드"
HOME_TITLE = "대출상품 조건과 신용관리 정보 안내"
HOME_DESC = ("직장인대출, 무직자대출, 비상금대출, 소액대출, 저신용자대출 등 다양한 대출상품의 조건과 "
             "신용점수, 상환관리, 불법 대출 주의사항을 쉽게 정리한 생활금융 정보 사이트입니다.")

HOME_FAQ = [
    ("무직자도 대출을 알아볼 수 있나요?",
     "일부 금융상품은 소득 증빙이 부족한 사람도 조회할 수 있지만, 실제 가능 여부는 신용점수, 기존 대출, 연체 이력, 금융회사 심사 기준에 따라 달라집니다."),
    ("대출 조회를 하면 신용점수가 떨어지나요?",
     "일반적인 단순 조회와 실제 대출 신청, 다중 신청 여부에 따라 영향이 다를 수 있습니다. 정확한 내용은 이용하는 금융회사와 신용평가 기준을 확인해야 합니다."),
    ("당일대출은 정말 가능한가요?",
     "당일 진행이 가능한 상품도 있을 수 있지만, 심사 시간, 서류 제출, 영업시간, 개인 신용상태에 따라 달라질 수 있습니다."),
    ("저신용자대출은 무엇을 가장 조심해야 하나요?",
     "높은 금리, 불법 중개수수료, 선입금 요구, 개인정보 과다 요구, 무등록 업체 여부를 먼저 확인해야 합니다."),
    ("이 사이트에서 대출 신청이 가능한가요?",
     "본 사이트는 대출을 직접 제공하거나 중개하지 않으며, 일반적인 금융정보를 안내하는 정보 사이트입니다."),
]


def home_schema():
    """홈 화면에 실제로 보이는 내용과 일치하는 구조화 데이터."""
    data = [
        {"@context": "https://schema.org", "@type": "WebSite",
         "name": SITE_NAME, "url": BASE_URL + "/",
         "description": HOME_DESC, "image": OG_IMAGE},
        {"@context": "https://schema.org", "@type": "Organization",
         "name": SITE_NAME, "url": BASE_URL + "/",
         "email": "88smartbro88@gmail.com", "logo": OG_IMAGE},
        {"@context": "https://schema.org", "@type": "FAQPage",
         "mainEntity": [
             {"@type": "Question", "name": q,
              "acceptedAnswer": {"@type": "Answer", "text": a}}
             for q, a in HOME_FAQ]},
    ]
    return "".join('<script type="application/ld+json">%s</script>\n'
                   % json.dumps(d, ensure_ascii=False) for d in data)


def home_page():
    prefix = ""

    def card(url, name, desc):
        return ('<a class="card" href="%s"><h3>%s</h3><p>%s</p></a>'
                % (rel(prefix, url), esc(name), esc(desc)))

    def pcard(slug):
        p = P[slug]
        return card("/loan/%s/" % slug, p["name"], p["summary"][:52] + "…")

    # 1. 히어로
    hero_buttons = [
        ("/target/", "내 조건별 대출 보기"),
        ("/safety/checklist/", "대출 전 체크리스트 보기"),
        ("/credit/credit-score/", "신용점수 관리법 보기"),
        ("/safety/illegal-loan/", "불법 대출 주의사항 보기"),
    ]
    hero = """
<section class="hero">
<h1>%s</h1>
<p>직장인대출, 무직자대출, 비상금대출, 소액대출, 저신용자대출 등 다양한 대출 유형의 조건과 주의사항을
한눈에 확인할 수 있도록 정리했습니다. 실제 가능 여부와 한도, 금리는 개인 신용상태와 금융회사 심사
기준에 따라 달라질 수 있습니다.</p>
<div class="hero-links">%s</div>
</section>""" % (esc(HOME_H1),
                 "".join('<a class="btn%s" href="%s">%s</a>'
                         % ("" if i == 0 else " btn-outline", rel(prefix, u), esc(n))
                         for i, (u, n) in enumerate(hero_buttons)))

    # 2. 대출상품 빠른 찾기 (전체 27개 카드)
    quick = ('<section id="quick"><h2>자주 찾는 대출상품 빠른 찾기</h2>'
             '<p>아래 카드에서 찾는 대출 유형을 선택하면 일반적인 조건, 필요서류, 주의사항을 확인할 수 있습니다. '
             '같은 이름의 대출이라도 금융회사별로 조건이 다르므로 비교 후 결정하는 것이 안전합니다.</p>'
             '<div class="card-grid card-grid-compact">%s</div></section>' % (
                 card("/loan/", "전체대출", "스피드대출에서 다루는 26가지 대출 유형을 한 페이지에서 비교할 수 있습니다.") +
                 "".join(pcard(p["slug"]) for p in PRODUCTS)))

    # 3. 내 상황에 맞는 대출 알아보기
    situations = [
        ("직장인이라면", [
            ("/loan/worker-loan/", "직장인대출 조건"),
            ("/loan/credit-loan/", "신용대출 확인사항"),
            ("/loan/refinance-loan/", "대환대출 체크리스트")]),
        ("소득 증빙이 어렵다면", [
            ("/loan/jobless-loan/", "무직자대출"),
            ("/loan/housewife-loan/", "주부대출"),
            ("/loan/freelancer-loan/", "프리랜서대출"),
            ("/loan/daily-worker-loan/", "일용직대출")]),
        ("사업을 운영 중이라면", [
            ("/loan/business-loan/", "사업자대출"),
            ("/loan/self-employed-loan/", "자영업자대출"),
            ("/loan/professional-loan/", "전문직대출")]),
        ("신용점수가 낮다면", [
            ("/loan/low-credit-loan/", "저신용자대출"),
            ("/loan/rehabilitation-loan/", "회생파산대출"),
            ("/guide/rejection/", "대출 거절 이유")]),
    ]
    situ_cols = "".join(
        '<div class="situ-col"><h3>%s</h3><ul>%s</ul></div>'
        % (esc(t), "".join('<li><a href="%s">%s</a></li>' % (rel(prefix, u), esc(n)) for u, n in links))
        for t, links in situations)
    situ = ('<section id="situations"><h2>내 상황에 맞는 대출 알아보기</h2>'
            '<p>직업과 소득 형태, 신용 상태에 따라 검토할 수 있는 대출이 다릅니다. '
            '내 상황에 가까운 항목부터 확인해 보세요.</p>'
            '<div class="situ-grid">%s</div></section>' % situ_cols)

    # 4. 신청방식별 대출 차이
    method_desc = [
        ("mobile-loan", "스마트폰 앱으로 조회와 신청이 가능한 대출 유형입니다."),
        ("online-loan", "방문 없이 인터넷으로 조건을 확인하는 방식입니다."),
        ("untact-loan", "상담이나 서류 제출 과정이 비대면으로 진행될 수 있는 대출입니다."),
        ("no-visit-loan", "영업점 방문 없이 진행되는 대출 유형을 말합니다."),
        ("same-day-loan", "당일 입금을 의미하는 경우가 많지만, 실제 가능 여부는 심사와 영업시간에 따라 달라질 수 있습니다."),
    ]
    method_items = "".join(
        '<div class="method-item"><a href="%s"><strong>%s</strong></a><p>%s</p></div>'
        % (rel(prefix, "/loan/%s/" % s), esc(P[s]["name"]), esc(d))
        for s, d in method_desc)
    method = ('<section id="methods"><h2>신청방식별 대출 차이</h2>'
              '<p>같은 대출이라도 신청 방법에 따라 절차와 확인사항이 다릅니다. '
              '용어가 비슷해 보여도 차이가 있으므로 신청 전에 구분해 두면 좋습니다.</p>'
              '<div class="method-list">%s</div></section>' % method_items)

    # 5. 대출 전 반드시 확인할 5가지
    checks = [
        ("/guide/limit-rate/", "실제 금리와 연체이자율 — 광고 속 최저금리가 아니라 내 조건으로 조회한 금리를 확인하세요."),
        ("/guide/conditions/", "중도상환수수료 여부 — 미리 갚을 때 수수료가 있는지, 면제 조건은 무엇인지 확인하세요."),
        ("/credit/repayment-plan/", "월 상환금과 상환기간 — 월 상환액이 실수령액의 30%를 넘지 않는지 계산해 보세요."),
        ("/credit/credit-score/", "기존 대출과 신용점수 영향 — 추가 대출이 신용점수와 추후 대출 한도에 주는 영향을 확인하세요."),
        ("/safety/brokerage-fee/", "불법 중개수수료와 개인정보 요구 여부 — 수수료 선입금이나 과도한 개인정보 요구는 불법·사기 신호입니다."),
    ]
    check_lis = "".join('<li><a href="%s">%s</a></li>' % (rel(prefix, u), esc(t)) for u, t in checks)
    check = ('<section class="check-section" id="checklist"><h2>대출 전 반드시 확인할 5가지</h2>'
             '<p>어떤 대출이든 신청 전에 아래 다섯 가지는 반드시 확인하는 것이 좋습니다. '
             '항목을 누르면 자세한 설명으로 이동합니다.</p>'
             '<ol class="check-list">%s</ol>'
             '<p><a href="%s">→ 10가지 전체 체크리스트 보기</a></p></section>'
             % (check_lis, rel(prefix, "/safety/checklist/")))

    # 6. 신용점수·상환관리 가이드
    credit_links = [
        ("/guide/credit-story/", "신용점수 조회하면 점수가 떨어질까?"),
        ("/guide/rejection/", "대출 거절되는 대표적인 이유"),
        ("/loan/refinance-loan/", "대환대출이 항상 유리하지 않은 이유"),
        ("/credit/overdue-check/", "연체 전 확인해야 할 상환 방법"),
        ("/loan/small-loan/", "소액대출도 신용점수에 영향이 있을까?"),
    ]
    credit_sec = ('<section id="credit"><h2>신용점수와 상환관리 가이드</h2>'
                  '<p>대출은 받는 것보다 갚는 계획이 더 중요합니다. 신용점수가 매겨지는 원리와 '
                  '연체 없이 상환을 관리하는 방법을 정리했습니다.</p>'
                  '<ul class="link-list">%s</ul></section>'
                  % "".join('<li><a href="%s">%s</a></li>' % (rel(prefix, u), esc(n)) for u, n in credit_links))

    # 7. 금융안전·대출사기 예방
    safety_links = [
        ("/safety/illegal-loan/", "불법 대출업체 구별하는 방법"),
        ("/safety/personal-info/", "대출 상담 전 개인정보 요구 주의사항"),
        ("/safety/loan-fraud/", "선입금 요구 대출이 위험한 이유"),
        ("/safety/brokerage-fee/", "불법 중개수수료를 요구받았을 때 대처법"),
        ("/safety/high-interest/", "고금리 대출 전 확인해야 할 사항"),
    ]
    safety_sec = ('<section id="safety"><h2>불법 대출과 금융사기 주의사항</h2>'
                  '<p>급하게 돈이 필요할수록 불법 사금융과 대출 사기에 노출되기 쉽습니다. '
                  '거래 전에 아래 내용을 꼭 확인하세요. 피해가 의심되면 금융감독원 1332로 신고할 수 있습니다.</p>'
                  '<ul class="link-list">%s</ul></section>'
                  % "".join('<li><a href="%s">%s</a></li>' % (rel(prefix, u), esc(n)) for u, n in safety_links))

    # 8. 최신 대출가이드
    guide_cards = "".join(card("/guide/%s/" % g["slug"], g["name"], g["summary"][:56] + "…")
                          for g in GUIDE_ARTICLES[:6])
    guides = ('<section id="guides"><h2>최신 대출가이드</h2>'
              '<p>대출 기초 용어부터 한도와 금리가 정해지는 원리, 필요서류, 거절 사유까지 — '
              '대출을 처음 알아보는 분을 위한 가이드입니다. 각 글에는 정보 기준일을 표시하며 제도 변경 시 갱신합니다.</p>'
              '<div class="card-grid">%s</div>'
              '<p><a href="%s">→ 대출가이드 전체보기</a></p></section>'
              % (guide_cards, rel(prefix, "/guide/")))

    # 9. 콘텐츠 신뢰 정보
    trust_links = [("/about/author/", "작성자 소개"), ("/about/editorial/", "콘텐츠 작성 기준"),
                   ("/about/disclaimer/", "면책고지"), ("/about/contact/", "문의하기"),
                   ("/about/privacy/", "개인정보처리방침")]
    trust = ('<section class="trust-box" id="trust"><h2>이 사이트의 금융정보 작성 기준</h2>'
             '<ul>'
             '<li>본 사이트는 대출을 직접 제공하거나 중개하지 않습니다.</li>'
             '<li>모든 콘텐츠는 일반적인 금융정보 제공을 목적으로 작성됩니다.</li>'
             '<li>대출 가능 여부, 한도, 금리, 승인 여부는 개인 신용상태와 금융회사 심사 기준에 따라 달라질 수 있습니다.</li>'
             '<li>콘텐츠는 금융 관련 공공자료, 금융회사 공시자료, 소비자 보호 자료 등을 참고해 작성하며, '
             '변경 가능성이 있는 정보는 주기적으로 수정합니다. (정보 기준일: %s)</li>'
             '</ul><nav class="trust-links">%s</nav></section>'
             % (esc(BASELINE_DATE),
                " · ".join('<a href="%s">%s</a>' % (rel(prefix, u), esc(n)) for u, n in trust_links)))

    # 10. FAQ (구조화 데이터와 동일한 내용)
    faq_html = "".join("<details><summary>%s</summary><p>%s</p></details>" % (esc(q), esc(a))
                       for q, a in HOME_FAQ)
    faq = '<section class="faq" id="faq"><h2>대출정보 자주 묻는 질문</h2>%s</section>' % faq_html

    home_toc = toc_aside([
        ("#quick", "대출상품 빠른 찾기"),
        ("#situations", "상황에 맞는 대출"),
        ("#methods", "신청방식별 차이"),
        ("#checklist", "대출 전 확인 5가지"),
        ("#credit", "신용·상환관리"),
        ("#safety", "금융사기 주의"),
        ("#guides", "최신 대출가이드"),
        ("#trust", "정보 작성 기준"),
        ("#faq", "자주 묻는 질문"),
    ])
    content = "\n".join([
        ad_slot("home_top"),          # 광고 1: 히어로 설명문 아래, 대출상품 카드 위
        quick, situ, method,
        ad_slot("home_middle"),       # 광고 2: 신청방식별 대출 비교 아래
        check, credit_sec, safety_sec, guides,
        ad_slot("home_bottom"),       # 광고 3: 최신 대출가이드 아래
        trust, faq,
        article_disclaimer()])
    body = hero + '\n<div class="page-grid">%s<div class="page-content">%s</div></div>' % (home_toc, content)
    write("/index.html", page("/", HOME_TITLE, HOME_DESC, body, 0, head_extra=home_schema(), wide=True))
    URLS.append("/")


# ──────────────────────────── 빌드 ────────────────────────────

def build():
    if os.path.exists(OUT):
        shutil.rmtree(OUT)
    os.makedirs(OUT)

    # 정적 자원
    for asset in ("style.css", "script.js", "og-image.png"):
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

    # ads.txt — 애드센스 게시자 ID 설정 시 자동 생성
    if ADSENSE_CLIENT:
        pub_id = ADSENSE_CLIENT.replace("ca-", "")
        write("/ads.txt", "google.com, %s, DIRECT, f08c47fec0942fa0\n" % pub_id)

    mirror_to_root()
    print("생성 완료: %d개 페이지 → docs/ 및 저장소 루트" % len(set(URLS)))


def mirror_to_root():
    """docs/ 출력을 저장소 루트에도 복사한다.

    Cloudflare Pages 등에서 빌드 출력 디렉터리를 설정하지 않아도(기본 '/')
    사이트가 바로 서빙되도록 하기 위함. 출력 디렉터리를 docs로 지정해도 동작한다.
    """
    for entry in os.listdir(OUT):
        src = os.path.join(OUT, entry)
        dst = os.path.join(ROOT, entry)
        if os.path.isdir(src):
            if os.path.exists(dst):
                shutil.rmtree(dst)
            shutil.copytree(src, dst)
        else:
            shutil.copy(src, dst)


def ensure_assets_dir(asset):
    d = os.path.join(OUT, "assets")
    os.makedirs(d, exist_ok=True)
    return os.path.join(d, asset)


if __name__ == "__main__":
    build()
