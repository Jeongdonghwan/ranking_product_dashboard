현재 코드를 상세히 분석했습니다. 중요한 발견사항이 있습니다:
현재 시스템 분석 결과
1. 현재 필수 컬럼 (영문)
required_cols = ['date', 'campaign_name', 'spend', 'clicks', 'conversions', 'revenue']
2. 문제점
템플릿과 코드 불일치: 코드는 영문 컬럼을 기대하지만, 한국어 템플릿을 제공해야 함
한→영 매핑 로직 없음: 업로드 시 한국어 컬럼을 영문으로 변환하는 로직이 없음
리드형(잠재고객) 미지원: 현재 매출형(ROAS)만 지원, 리드형(CPL) 계산 로직 없음
광고유형(ad_type) 컬럼 없음: 매출형/잠재고객 구분 불가
3. 현재 계산되는 지표
ROAS, CTR, CPC, CPA, CVR, 객단가
모두 매출 기반 지표임
간소화된 통합 템플릿 설계
템플릿 컬럼 (총 8개, 최소화)
순서	한국어 컬럼명	영문 매핑	필수	비고
1	날짜	date	✓	YYYY-MM-DD
2	캠페인명	campaign_name	✓	-
3	광고유형	ad_type	✓	매출형/잠재고객
4	지출액	spend	✓	원
5	노출수	impressions	선택	없으면 추정
6	클릭수	clicks	✓	-
7	전환수	conversions	✓	구매 or 리드
8	매출액	revenue	조건부	잠재고객은 0 입력
Excel 템플릿 구조 (단순화)
Sheet 1: 입력양식 (헤더 + 샘플 4줄)
날짜 | 캠페인명 | 광고유형 | 지출액 | 노출수 | 클릭수 | 전환수 | 매출액
Sheet 2: 가이드 (간단 설명)
광고유형: "매출형" 또는 "잠재고객" 입력
매출형: 구매 전환 캠페인 (ROAS 계산)
잠재고객: 리드 수집 캠페인 (CPL 계산, 매출액에 0 입력)
Claude’s Plan
계획: 간소화된 통합 템플릿 및 기능 검증
Phase 1: 통합 Excel 템플릿 생성
파일: app/static/templates/ad_template_unified.xlsx Sheet 1: 입력양식
날짜	캠페인명	광고유형	지출액	노출수	클릭수	전환수	매출액
2024-11-01	블프_매출	매출형	150000	45000	1200	48	540000
2024-11-01	리드_상담	잠재고객	100000	30000	800	120	0
Sheet 2: 가이드 (컬럼 설명 + 예시)
Phase 2: 업로드 로직 수정
파일: app/routes/ad_analysis.py
한→영 컬럼 매핑 추가
COLUMN_MAPPING = {
    '날짜': 'date',
    '캠페인명': 'campaign_name',
    '광고유형': 'ad_type',
    '지출액': 'spend',
    '노출수': 'impressions',
    '클릭수': 'clicks',
    '전환수': 'conversions',
    '매출액': 'revenue'
}
광고유형 값 변환
AD_TYPE_MAPPING = {'매출형': 'sales', '잠재고객': 'lead'}
업로드 함수에 컬럼 변환 로직 추가
Phase 3: 메트릭스 계산 분기
파일: app/routes/ad_analysis.py - _calculate_metrics_inmemory() 수정
매출형 캠페인: ROAS, CPA, CVR, 객단가
잠재고객 캠페인: CPL (지출액/전환수), 리드전환율
캠페인별 광고유형 표시
Phase 4: 프론트엔드 표시 분기
파일: app/static/js/ad_dashboard.js
캠페인 테이블에 광고유형 컬럼 추가
매출형: ROAS, 매출액 표시
잠재고객: CPL, 리드수 표시
Phase 5: Playwright 기능 테스트
파일: tests/test_ad_dashboard.py
템플릿 다운로드 테스트
파일 업로드 테스트 (매출형 + 잠재고객 혼합)
수기 입력 테스트
저장/불러오기 테스트
기간 비교 테스트
변경 파일 목록
파일	작업
app/static/templates/ad_template_unified.xlsx	신규 생성
app/routes/ad_analysis.py	컬럼 매핑 + 광고유형 분기 추가
app/static/js/ad_dashboard.js	광고유형별 표시 분기
tests/test_ad_dashboard.py	신규 생성
User approved the plan
Update Todos

통합 Excel 템플릿 생성 (ad_template_unified.xlsx)

ad_analysis.py에 한→영 컬럼 매핑 로직 추가

_calculate_metrics_inmemory()에 광고유형 분기 추가

ad_dashboard.js에 광고유형별 표시 분기 추가

Playwright 테스트 스크립트 작성
먼저 통합 Excel 템플릿을 생성하겠습니다. Python 스크립트로 Excel 파일을 만들겠습니다.
이어서 진행해
Globpattern: "app/static/templates/*.xlsx"
⎿
No files found
Bash
⎿
Check templates directory
IN
dir "c:\Users\JDH\Downloads\insight\app\static\templates" 2>nul || echo "Directory not found"
OUT
ad_template_advanced.xlsx  ad_template_standard.xlsx
ad_template_basic.xlsx	   TEMPLATE_GUIDE.md
기존 템플릿 파일들이 있습니다. 현재 템플릿 구조를 확인하고, 통합 템플릿을 생성하겠습니다.
Read c:\Users\JDH\Downloads\insight\app\static\templates\TEMPLATE_GUIDE.md