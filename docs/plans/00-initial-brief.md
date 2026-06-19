# Day 38 — 간단 가계부 · 학생 용돈 기입장

## 토픽
- **#038** (실과) — 학생이 용돈 수입·지출을 입력하여 한 달 합계와 카테고리 분포를 시각화한다.

## 핵심 콘텐츠 목표
- 4~6학년 학생이 1:1로 사용. 자기 용돈 흐름을 직접 기록해 보며 합리적 소비를 익힌다.

## 포함 기능 (원 spec)
1. 거래 입력 — 날짜·항목·금액·카테고리·수입/지출
2. 월·주 그래프
3. JSON 내보내기(다른 PC로 이동)

## 배제 기능 (원 spec)
- 실제 결제, 은행 연동
- 가족 데이터 결합

## 기술 결정
- **Stack**: 단일 `index.html` + 자체완비 vanilla CSS + 순수 JS
- **차트**: Chart.js 대신 자체 Canvas 도넛/바 차트 (CDN 차단 환경 대비)
- **저장**: `localStorage` (`piggybank-38-v1` 키)
- **AI**: 사용하지 않음 (Gemini 호출 0건)
- **외부 의존성**: 0 (시스템 폰트 스택)
- **접근성**: 대비 4.5:1↑, focus state, aria-label, 키보드 동작 보장

## 디자인
- **Primary brand**: Revolut (cobalt violet `#494fdf` + true black `#000` canvas + white catalogue 모드)
- **Sub**: Mastercard 톤 (warm orange/red accent, 거래 카테고리 highlight)

## 개인정보
- 학생 이름·번호·사진 입력 받지 않음. 모든 데이터는 localStorage 단독 저장.
- JSON 내보내기는 사용자 선택 시점에만 다운로드로 노출.
