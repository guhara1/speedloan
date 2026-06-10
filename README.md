# 스피드대출 — 대출 정보 사이트

대출상품의 조건·필요서류·주의사항을 안내하는 **애드센스 수익형 대출 정보 사이트**입니다.
대출을 직접 제공·중개하지 않는 정보 안내 사이트 구조로 만들어져 있습니다.

## 폴더 구조

```
├─ generate.py            # 정적 사이트 생성 스크립트
├─ content_products.py    # 대출상품 26종 콘텐츠 (페이지당 1개 URL)
├─ content_articles.py    # 신용·상환관리 / 금융안전 / 대출가이드 콘텐츠
├─ content_about.py       # 사이트안내 페이지 + 필수 면책 문구
├─ assets/                # 공통 CSS / JS 원본
└─ docs/                  # 생성된 사이트 (배포 대상, 총 61페이지)
```

## 사이트 빌드

콘텐츠를 수정한 뒤 아래 명령으로 `docs/`를 다시 생성합니다.

```bash
python3 generate.py
```

별도 패키지 설치가 필요 없습니다 (Python 3 표준 라이브러리만 사용).

## 배포 (GitHub Pages)

1. 저장소 **Settings → Pages → Build and deployment**
2. Source: `Deploy from a branch`, Branch: 기본 브랜치 + `/docs` 폴더 선택
3. 커스텀 도메인을 연결한 경우 `generate.py`의 `BASE_URL`을 실제 도메인으로 바꾸고
   다시 빌드하세요 (sitemap.xml과 canonical 태그에 사용됩니다).

## 메뉴 구조

```
홈
├─ 대출상품 (26종 메가메뉴: 인기상품 / 직업·대상별 / 신청방식 / 담보·상환)
├─ 대상별 대출        → /loan/ 상품 페이지로 링크 (중복 URL 없음)
├─ 신청방식별 대출    → /loan/ 상품 페이지로 링크
├─ 담보·목적별 대출   → /loan/ 상품 페이지로 링크
├─ 신용·상환관리 (/credit/) — 신용점수 관리, 연체 전 확인사항, 상환계획, 금리 비교
├─ 금융안전 (/safety/) — 불법 대출 구별법, 사기 예방, 체크리스트 등 7편
├─ 대출가이드 (/guide/) — 기초상식, 한도와 금리, 필요서류 등 8편
└─ 사이트안내 (/about/) — 소개, 작성자, 작성 기준, 문의, 개인정보처리방침, 이용약관, 면책고지, 광고·제휴
```

모든 상품 페이지는 `/loan/<slug>/` **단일 URL**로만 존재하며, 대상별·신청방식별·담보목적별
메뉴는 같은 URL로 링크만 연결해 중복 콘텐츠 문제를 방지합니다.

## 콘텐츠 추가 방법

- **상품 페이지 추가**: `content_products.py`의 `PRODUCTS`에 항목을 추가하고,
  필요하면 메뉴 그룹(`TARGET_MENU`, `MEGA_GROUPS` 등)에 슬러그를 넣은 뒤 재빌드
- **가이드 글 추가**: `content_articles.py`의 `GUIDE_ARTICLES` 등에 추가 후 재빌드
- 모든 페이지 푸터에 면책 문구(`content_about.py`의 `DISCLAIMER`)가 자동 포함됩니다.

## 애드센스 적용 메모

- 승인 신청 전 `about/` 페이지(개인정보처리방침·면책고지 포함)가 모두 게시된 상태인지 확인
- 승인 후 애드센스 코드는 `generate.py`의 `page()` 함수 `<head>` 부분에 추가하고 재빌드
- `ads.txt`는 `docs/ads.txt`로 직접 추가 (재빌드 시 `docs/`가 초기화되므로,
  영구 반영하려면 `generate.py`의 `build()`에서 함께 생성하도록 추가하세요)
