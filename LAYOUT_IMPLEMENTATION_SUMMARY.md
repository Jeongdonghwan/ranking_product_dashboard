# 광고 분석 대시보드 - 단일 페이지 통합 레이아웃 구현 가이드

## 개요
7개 분리 탭 → 1개 스크롤 페이지로 전환

## 물리적 구조

### Grid Layout (2열)
```
┌─────────────────────────────┬────────────┐
│  Main Content (scrollable)   │ Sidebar    │
│  1fr                         │ 320px fix  │
└─────────────────────────────┴────────────┘
```

### Sticky Header (항상 보임)
- 제목, 부제목
- 액션 버튼: 📤업로드 ✏️수기 💾저장 📄PDF 📊Excel
- 필터: 오늘/7일/30일/사용자정의

## 메인 콘텐츠 구성 (위 → 아래)

1. **Metrics Cards** (8개: 지출/매출/ROAS/전환/노출/클릭/CTR/CVR)
   - auto-grid: minmax(140px, 1fr)
   - 컬러 코드: 파란/초록/주황/보라

2. **Daily Trend Chart** (Full Width)
   - 높이: 350px
   - 라인+막대 혼합: ROAS, CTR, 지출

3. **Distribution Charts** (2x1)
   - ROAS 히스토그램
   - 예산 원형 차트

4. **Funnel & Comparison** (2x1)
   - 전환 깔때기
   - 캠페인 막대 차트

5. **Weekday Heatmap** (Full Width)
   - 7칸 그리드 x 2행 (ROAS, CTR)
   - 색상: low/medium/high

6. **CREATIVE ANALYSIS ⭐** (HIGHLIGHTED)
   - 파란 테두리, 그라데이션 배경
   - 4 탭: Top ROAS | Top CVR | All | Low Performers
   - 각 탭별 테이블

7. **Campaign Table** (Full Width)
   - 순위/캠페인명/ROAS/CTR/CVR/CPA/지출/상태/액션
   - 정렬 가능: ROAS/지출/매출

8. **AI Insights** (Full Width)
   - 텍스트 영역
   - 재생성 버튼

## 오른쪽 사이드바 (고정, sticky top)

### Section 1: 저장된 분석
- 최근 2-3개 목록
- "더 보기" → 모달

### Section 2: 기간 비교
- Select A, Select B
- 비교 실행 버튼
- 결과 표시 영역 (hidden)

### Section 3: 목표 관리
- 월 입력
- 예산 입력
- ROAS 목표
- 저장 버튼
- 예산 소진 현황 표시

## 모달 (5개)

1. **Upload Modal**: 파일 드롭 + 템플릿
2. **Manual Input Modal**: 폼 + 미리보기
3. **Save Analysis Modal**: 이름/태그/메모
4. **Saved Analyses List Modal**: 전체 목록
5. **Campaign Details Modal**: 캠페인 상세

## CSS 클래스 매핑

### Layout
- `.dashboard-wrapper`: grid: 1fr 320px
- `.main-scroll`: overflow-y: auto
- `.sidebar-panel`: position: sticky, height: 100vh
- `.sticky-header`: position: sticky, top: 0, z-index: 100
- `.main-container`: max-width: 1200px, margin: 0 auto

### Sections
- `.section`: white card, shadow, rounded
- `.section-header`: padding, border-bottom, flex
- `.section-content`: padding
- `.section-title`: flex, gap
- `.section-icon`: font-size: 18px

### Metrics
- `.metrics-grid`: grid: auto-fit, minmax(140px, 1fr)
- `.metric-card`: gradient bg
- `.metric-card.green/orange/red/purple`: colors

### Tables
- `.table-wrapper`: overflow-x: auto
- `.badge-success/warning/danger/neutral`: status

### Creative
- `.creative-analysis-highlight`: blue border, gradient bg
- `.creative-analysis-badge`: "⭐ 핵심 분석"
- `.section-tabs`: flex tabs
- `.section-tab.active`: blue underline
- `.creative-tab.active`: display: block

### Sidebar
- `.sidebar-section`: border-bottom
- `.sidebar-section-header`: bg-hover, uppercase
- `.sidebar-section-content`: flex, flex-direction: column
- `.sidebar-item`: hover effect, active state

### Charts
- `.charts-grid`: grid: 2fr
- `.chart-container`: position: relative, height: 350px
- `.full-width`: grid-column: 1 / -1

### Heatmap
- `.heatmap-container`: grid: 7fr
- `.heatmap-cell.low/medium/high`: colors

### Modals
- `.modal`: position: fixed, z-index: 1000, rgba bg
- `.modal.active`: display: flex
- `.modal-content`: white bg, padding, shadow

## 반응형

### Desktop (>1400px)
- Grid: 1fr 320px
- Charts: 2단
- Metrics: auto-fit

### Tablet (1200-1400px)
- Grid: 1fr (sidebar 숨김)
- Charts: 1단

### Mobile (<768px)
- Full stack
- Metrics: 2단
- Header: icons만
- Sidebar: hidden

## JavaScript 함수

### 초기화
- `initDashboard()`: 시작
- `initTabs()`: 크리에이티브 탭
- `initUploadArea()`: 파일 드롭
- `initDateFilter()`: 날짜 필터

### 데이터
- `loadMetrics()`: 지표 카드
- `loadCharts()`: 모든 차트
- `loadCreativeAnalysis()`: 크리에이티브
- `loadCampaigns()`: 캠페인 테이블
- `loadAIInsights()`: AI 인사이트
- `loadSavedAnalyses()`: 저장 목록

### 필터
- `setDateRange(type)`: today/7days/30days/custom
- `applyCustomDateRange()`: 사용자정의 적용

### UI
- `switchCreativeTab(tabName)`: 크리에이티브 탭 전환
- `sortCampaigns(sortBy)`: 캠페인 정렬

### 모달
- `openUploadModal()` / `closeUploadModal()`
- `openManualInputModal()` / `closeManualInputModal()`
- `openSaveModal()` / `closeSaveModal()`
- `openSavedAnalysesModal()` / `closeSavedAnalysesModal()`
- `openCampaignDetailsModal(id)` / `closeCampaignDetailsModal()`

### 액션
- `uploadFile(file)`: 파일 업로드
- `addManualDataRow(event)`: 수기 데이터 추가
- `submitManualData()`: 수기 제출
- `saveCurrentAnalysis()`: 분석 저장
- `confirmSave()`: 저장 확인
- `compareAnalysis()`: 기간 비교
- `saveGoal()`: 목표 저장
- `loadBudgetPacing()`: 예산 소진 로드
- `exportPDF()` / `exportExcel()`: 내보내기
- `downloadTemplate(type)`: 템플릿 다운로드
- `regenerateInsights()`: AI 재생성

## 색상 시스템

### Primary
- `--primary-blue: #1a73e8`

### Accent
- `--accent-green: #0f9d58` (수익/ROAS)
- `--accent-orange: #f9ab00` (CPA/Cost)
- `--accent-red: #ea4335` (낮은 성과)
- `--accent-purple: #9c27b0` (CTR)

### Neutral
- `--bg-primary: #f8f9fa`
- `--bg-secondary: #ffffff`
- `--bg-hover: #f1f3f4`
- `--border-color: #dadce0`
- `--text-primary: #202124`
- `--text-secondary: #5f6368`

## 핵심: 크리에이티브 분석 강조

### 시각적 강조
✅ 파란 2px 테두리
✅ 밝은 그라데이션 배경
✅ "⭐ 핵심 분석" 배지
✅ 다른 섹션과 분리

### 4개 탭으로 깊이
💎 Top ROAS: 수익 성과
🎯 Top CVR: 전환 성과
📋 All Creatives: 전체 보기
⚠️ Low Performers: 개선 대상

### 위치
히트맵 이후, 캠페인 테이블 이전
→ 스크롤 진행 중 자연스럽게 진입

## 구현 체크리스트

### Phase 1: Layout
- [ ] Grid 레이아웃 (1fr 320px)
- [ ] Sticky header 구현
- [ ] Main container (max-width)
- [ ] Sidebar (sticky top, 100vh)

### Phase 2: Sections
- [ ] Metrics grid
- [ ] Chart containers (5개)
- [ ] Heatmap (7x2)
- [ ] Creative section (highlighted)
- [ ] Campaign table
- [ ] AI insights

### Phase 3: Interactivity
- [ ] 날짜 필터 토글
- [ ] 크리에이티브 탭
- [ ] 캠페인 정렬
- [ ] 모달 열기/닫기
- [ ] 사이드바 섹션 토글

### Phase 4: Responsive
- [ ] Desktop: sidebar 표시
- [ ] Tablet: sidebar 숨김, charts 1단
- [ ] Mobile: full stack

### Phase 5: Data
- [ ] API 호출
- [ ] 동적 로딩
- [ ] 에러 처리
- [ ] 로딩 상태

## 파일 목록

1. **HTML**: `ad_dashboard_unified.html`
   - 완전한 HTML 구조
   - Inline CSS (전체 스타일)
   - Script placeholder

2. **JavaScript**: `ad_dashboard_unified.js`
   - 모든 초기화 함수
   - 데이터 로드 함수
   - 이벤트 핸들러
   - Chart.js 통합

3. **Design Doc**: `UNIFIED_LAYOUT_DESIGN.md`
   - 상세한 구조 설명
   - CSS 클래스 참고
   - 반응형 정보
   - 함수 목록

## 다음 단계

1. HTML 파일 생성 (구조)
2. CSS 추가 (스타일링)
3. JavaScript 작성 (기능)
4. Chart.js 통합
5. API 연동
6. 테스트
7. 배포

