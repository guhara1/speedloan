# -*- coding: utf-8 -*-
"""IndexNow 일괄 전송 — 네이버·빙 등 IndexNow 참여 검색엔진에 URL을 즉시 통보.

사용법 (인터넷이 되는 PC에서):
    python3 ping_indexnow.py            # 사이트 전체 URL 전송
    python3 ping_indexnow.py /loan/jobless-loan/   # 특정 URL만 전송 (새 글 발행 시)

- 구글은 IndexNow에 참여하지 않으므로 이 스크립트로는 색인되지 않습니다.
  (구글: Search Console 사이트맵 + URL 검사 / ping_google_indexing.py 참고)
- 키 파일은 generate.py 빌드 시 사이트 루트에 자동 배치됩니다.
"""
import json
import sys
import urllib.request

from generate import BASE_URL, INDEXNOW_KEY

HOST = BASE_URL.split("//", 1)[1]

# IndexNow 참여 엔진 공용 엔드포인트(한 곳에 보내면 참여 엔진 전체에 전파됨)
ENDPOINTS = [
    "https://api.indexnow.org/indexnow",
    "https://searchadvisor.naver.com/indexnow",  # 네이버 직접 엔드포인트
]


def all_urls():
    import re
    sm = open("docs/sitemap.xml", encoding="utf-8").read()
    return re.findall(r"<loc>(.*?)</loc>", sm)


def main():
    if len(sys.argv) > 1:
        urls = [BASE_URL + a if a.startswith("/") else a for a in sys.argv[1:]]
    else:
        urls = all_urls()
    payload = json.dumps({
        "host": HOST,
        "key": INDEXNOW_KEY,
        "keyLocation": "%s/%s.txt" % (BASE_URL, INDEXNOW_KEY),
        "urlList": urls,
    }).encode("utf-8")

    for ep in ENDPOINTS:
        req = urllib.request.Request(ep, data=payload,
                                     headers={"Content-Type": "application/json; charset=utf-8"})
        try:
            with urllib.request.urlopen(req, timeout=15) as r:
                print("%s → HTTP %d" % (ep, r.status))
        except Exception as e:
            print("%s → 실패: %s" % (ep, e))
    print("전송 URL %d건" % len(urls))


if __name__ == "__main__":
    main()
