# -*- coding: utf-8 -*-
"""구글 Indexing API 일괄 전송 스크립트.

⚠️ 솔직한 안내
- 구글 Indexing API는 공식적으로 채용공고(JobPosting)·라이브방송(BroadcastEvent)
  페이지 전용입니다. 일반 정보 페이지에 사용하는 것은 가이드라인 밖 사용이며,
  구글이 무시하거나 효과가 제한될 수 있습니다.
- 일반 페이지의 정석 루트는 ① Search Console 사이트맵 제출
  ② URL 검사 도구의 '색인 생성 요청' ③ 내부링크·RSS 발견입니다.
- 참고: 과거의 구글 sitemap ping 엔드포인트(google.com/ping)는 2023년 폐기되어
  더 이상 동작하지 않습니다(404). 별도 자동화가 불필요합니다.

사전 준비 (인터넷이 되는 PC에서):
  1. Google Cloud 콘솔에서 프로젝트 생성 → 'Indexing API' 사용 설정
  2. 서비스 계정 생성 → JSON 키 다운로드 (service_account.json)
  3. Search Console 속성(speedloan.pages.dev)의 '소유자'로
     서비스 계정 이메일을 추가
  4. pip install google-auth requests

사용법:
    python3 ping_google_indexing.py service_account.json                 # 전체 URL
    python3 ping_google_indexing.py service_account.json /loan/etc-loan/ # 특정 URL
"""
import json
import re
import sys

from generate import BASE_URL

ENDPOINT = "https://indexing.googleapis.com/v3/urlNotifications:publish"
SCOPES = ["https://www.googleapis.com/auth/indexing"]


def all_urls():
    sm = open("docs/sitemap.xml", encoding="utf-8").read()
    return re.findall(r"<loc>(.*?)</loc>", sm)


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    sa_path = sys.argv[1]
    try:
        from google.oauth2 import service_account
        from google.auth.transport.requests import AuthorizedSession
    except ImportError:
        print("필요 패키지 설치: pip install google-auth requests")
        sys.exit(1)

    creds = service_account.Credentials.from_service_account_file(sa_path, scopes=SCOPES)
    session = AuthorizedSession(creds)

    if len(sys.argv) > 2:
        urls = [BASE_URL + a if a.startswith("/") else a for a in sys.argv[2:]]
    else:
        urls = all_urls()

    ok = 0
    for u in urls:
        r = session.post(ENDPOINT, json={"url": u, "type": "URL_UPDATED"})
        status = "OK" if r.status_code == 200 else "HTTP %d %s" % (r.status_code, r.text[:120])
        if r.status_code == 200:
            ok += 1
        print("%s → %s" % (u, status))
    print("완료: %d/%d 성공 (일일 기본 할당량 200건 유의)" % (ok, len(urls)))


if __name__ == "__main__":
    main()
