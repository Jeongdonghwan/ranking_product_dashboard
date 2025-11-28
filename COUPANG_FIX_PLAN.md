# 쿠팡 광고 대시보드 개선 계획 (Ultra Think)

## 📊 현재 상황 분석

### 사용자 피드백 요약
1. **총광고비, 매출액, 평균ROAS가 안 맞음** ✅ 원인 파악 완료
2. **비검색영역 데이터가 포함됨** ✅ 원인 파악 완료
3. **광고비vs매출액분포 차트가 안 나옴** 🔍 조사 필요
4. **ROAS TOP 20이라면서 10개만 나옴** ✅ 코드 확인 완료
5. **상위 10개만 보여주면 됨** ✅ 변경 필요
6. **제외해야 될 키워드 추천 시스템 필요** 🎯 신규 기능
7. **추천 결과를 별도로 표시** 🎯 신규 기능

---

## 🔍 문제 원인 분석

### 문제 1: 메트릭스 불일치

**실제 Excel 데이터:**
```
전체 데이터 (229행):
- 광고비: 242,795원
- 매출: 567,660원
- ROAS: 233.79%

비검색영역 (29행) - 제외해야 함:
- 광고비: 188,455원 (전체의 77.6%!)
- 매출: 351,660원 (전체의 62.0%)

검색영역 (190행) - 분석 대상:
- 광고비: 41,942원
- 매출: 144,000원
- ROAS: 343.33%
```

**현재 백엔드 코드 문제점:**
```python
# app/routes/ad_analysis.py:263
df = df[df['키워드'] != '-'].copy()  # ❌ 키워드만 필터링
```

**올바른 필터링:**
```python
# '광고 노출 지면' 컬럼으로 필터링 필요
df = df[df['광고 노출 지면'] == '검색 영역'].copy()
df = df[df['키워드'] != '-'].copy()
```

---

### 문제 2: 비검색영역 포함

**Excel의 '광고 노출 지면' 컬럼 값:**
- `검색 영역` (190행) → **분석 대상**
- `비검색 영역` (29행) → **제외**
- `리타겟팅(외부 채널) - Product Ad` (10행) → **제외**

**비검색영역 특징:**
- 키워드가 대부분 `-` (빈 값)
- 광고비만 많고 전환 거의 없음
- ROAS 0%인 경우가 많음

---

### 문제 3: 산점도 차트 미표시

**예상 원인:**
1. 데이터가 없어서 (전환 없는 키워드가 182/190개)
2. Chart.js scatter plot 데이터 형식 오류
3. Canvas element가 숨겨져 있음

**디버깅 필요 사항:**
- `displayScatterChart()` 함수 호출 여부
- Chart.js 콘솔 에러 확인
- 데이터 포인트가 너무 적어서 안 보이는지 확인

---

### 문제 4: ROAS TOP 20 vs 10개 표시

**현재 코드 (ad_dashboard_coupang.html:803-860):**
```javascript
function displayROASBarChart(data) {
    // Sort by ROAS desc
    const sorted = [...data].sort((a, b) => (b.ROAS || 0) - (a.ROAS || 0));

    // TOP 10 + BOTTOM 10 = 20개
    const top10 = sorted.slice(0, 10);
    const bottom10 = sorted.slice(-10);
    const chartData = [...top10, ...bottom10];  // ❌ 20개
}
```

**사용자 요구사항:**
- TOP 10만 표시 (하위 10개 제거)

---

### 문제 5: 키워드 제외 추천 시스템 부재

**추천 대상 키워드 기준 (우선순위 순):**

1. **전환 없는 키워드 (182개)**
   - 광고비 지출했지만 매출 0원
   - 낭비 광고비: 39,447원 (94%)

2. **ROAS 50% 이하**
   - 투자 대비 절반도 못 버는 키워드

3. **CPC가 비정상적으로 높은 키워드**
   - 평균 CPC의 2배 이상

4. **클릭률(CTR)이 낮은 키워드**
   - 평균 CTR의 50% 이하

5. **광고비만 많고 클릭 적은 키워드**
   - 광고비 상위 20% but 클릭수 하위 50%

---

## 🎯 구현 계획

### Phase 1: 백엔드 데이터 필터링 수정 (최우선)

**파일:** `app/routes/ad_analysis.py`

**변경사항:**
```python
@ad_bp.route('/api/ad-analysis/upload-coupang', methods=['POST'])
def upload_coupang():
    try:
        df = pd.read_excel(file)

        # ✅ 1단계: 검색 영역만 필터링
        if '광고 노출 지면' in df.columns:
            df = df[df['광고 노출 지면'] == '검색 영역'].copy()
            logger.info(f'Filtered to 검색 영역: {len(df)} rows')

        # ✅ 2단계: 키워드 없는 행 제거
        df = df[df['키워드'] != '-'].copy()

        # ... 나머지 로직 동일
```

**예상 결과:**
- 총광고비: 41,942원 (현재: 잘못된 값)
- 총매출액: 144,000원
- 평균ROAS: 343.33% (현재: 199.63%)

---

### Phase 2: 키워드 제외 추천 시스템 구현

#### 2.1 백엔드 API 추가

**파일:** `app/routes/ad_analysis.py`

**신규 엔드포인트:**
```python
@ad_bp.route('/api/ad-analysis/coupang-recommendations', methods=['POST'])
def coupang_recommendations():
    """
    쿠팡 광고 키워드 제외 추천

    Request Body:
        {
            "data": [...],  # 키워드 데이터
            "criteria": {
                "min_roas": 50,     # ROAS 최소 기준
                "max_cpc": 1000,    # CPC 최대 기준
                "min_ctr": 0.5,     # CTR 최소 기준
                "min_clicks": 5     # 최소 클릭수
            }
        }

    Response:
        {
            "recommendations": [
                {
                    "keyword": "키워드명",
                    "reason": "전환 없음",
                    "priority": "high",
                    "spend": 1200,
                    "revenue": 0,
                    "roas": 0,
                    "waste": 1200
                },
                ...
            ],
            "summary": {
                "total_waste": 39447,
                "keywords_to_exclude": 182,
                "potential_savings": "94%"
            }
        }
    """
    data = request.json.get('data', [])
    criteria = request.json.get('criteria', {})

    df = pd.DataFrame(data)

    recommendations = []

    # 1. 전환 없는 키워드 (최우선)
    no_conversion = df[df['총 전환매출액(1일)'] == 0]
    for _, row in no_conversion.iterrows():
        recommendations.append({
            'keyword': row['키워드'],
            'reason': '전환 없음 (매출 0원)',
            'priority': 'high',
            'spend': row['광고비'],
            'revenue': 0,
            'roas': 0,
            'waste': row['광고비'],
            'clicks': row['클릭수'],
            'ctr': row['클릭률']
        })

    # 2. ROAS 낮은 키워드
    min_roas = criteria.get('min_roas', 50)
    low_roas = df[
        (df['총 전환매출액(1일)'] > 0) &
        (df['ROAS'] < min_roas)
    ]
    for _, row in low_roas.iterrows():
        waste = row['광고비'] - row['총 전환매출액(1일)']
        recommendations.append({
            'keyword': row['키워드'],
            'reason': f'ROAS {row["ROAS"]:.1f}% (기준: {min_roas}% 이상)',
            'priority': 'medium',
            'spend': row['광고비'],
            'revenue': row['총 전환매출액(1일)'],
            'roas': row['ROAS'],
            'waste': waste if waste > 0 else 0,
            'clicks': row['클릭수'],
            'ctr': row['클릭률']
        })

    # 3. CPC 비정상적으로 높은 키워드
    avg_cpc = df['CPC'].mean()
    max_cpc = criteria.get('max_cpc', avg_cpc * 2)
    high_cpc = df[df['CPC'] > max_cpc]
    for _, row in high_cpc.iterrows():
        if row['키워드'] not in [r['keyword'] for r in recommendations]:
            recommendations.append({
                'keyword': row['키워드'],
                'reason': f'CPC 과다 ({row["CPC"]:.0f}원, 평균: {avg_cpc:.0f}원)',
                'priority': 'low',
                'spend': row['광고비'],
                'revenue': row['총 전환매출액(1일)'],
                'roas': row.get('ROAS', 0),
                'waste': 0,
                'clicks': row['클릭수'],
                'ctr': row['클릭률'],
                'cpc': row['CPC']
            })

    # 4. CTR 낮은 키워드
    avg_ctr = df['클릭률'].mean()
    min_ctr = criteria.get('min_ctr', avg_ctr * 0.5)
    low_ctr = df[df['클릭률'] < min_ctr]
    for _, row in low_ctr.iterrows():
        if row['키워드'] not in [r['keyword'] for r in recommendations]:
            recommendations.append({
                'keyword': row['키워드'],
                'reason': f'CTR 낮음 ({row["클릭률"]:.2f}%, 평균: {avg_ctr:.2f}%)',
                'priority': 'low',
                'spend': row['광고비'],
                'revenue': row['총 전환매출액(1일)'],
                'roas': row.get('ROAS', 0),
                'waste': 0,
                'clicks': row['클릭수'],
                'ctr': row['클릭률']
            })

    # 우선순위별 정렬
    priority_order = {'high': 0, 'medium': 1, 'low': 2}
    recommendations.sort(key=lambda x: (priority_order[x['priority']], -x['waste']))

    # 요약 통계
    total_waste = sum(r['waste'] for r in recommendations)
    total_spend = df['광고비'].sum()

    summary = {
        'total_waste': int(total_waste),
        'keywords_to_exclude': len(recommendations),
        'potential_savings': f"{(total_waste / total_spend * 100):.1f}%" if total_spend > 0 else "0%",
        'high_priority': len([r for r in recommendations if r['priority'] == 'high']),
        'medium_priority': len([r for r in recommendations if r['priority'] == 'medium']),
        'low_priority': len([r for r in recommendations if r['priority'] == 'low'])
    }

    return jsonify({
        'success': True,
        'recommendations': recommendations,
        'summary': summary
    })
```

#### 2.2 프론트엔드 추천 섹션 추가

**파일:** `app/templates/ad_dashboard_coupang.html`

**추가할 HTML 섹션 (line 460 이후):**
```html
<!-- 키워드 제외 추천 섹션 -->
<div class="section" id="recommendationSection" style="display: none;">
    <div class="section-header">
        <h2 class="section-title">🎯 키워드 제외 추천</h2>
        <div class="section-actions">
            <button class="btn btn-secondary" onclick="exportRecommendations()">
                📥 추천 목록 다운로드
            </button>
            <button class="btn btn-danger" onclick="applyExclusions()">
                ❌ 선택 키워드 제외
            </button>
        </div>
    </div>

    <!-- 추천 요약 -->
    <div class="recommendation-summary" id="recSummary">
        <div class="summary-card highlight-red">
            <div class="summary-label">낭비 광고비</div>
            <div class="summary-value" id="recWaste">-</div>
            <div class="summary-unit">원</div>
        </div>
        <div class="summary-card highlight-orange">
            <div class="summary-label">제외 추천 키워드</div>
            <div class="summary-value" id="recCount">-</div>
            <div class="summary-unit">개</div>
        </div>
        <div class="summary-card highlight-green">
            <div class="summary-label">절감 가능 비용</div>
            <div class="summary-value" id="recSavings">-</div>
            <div class="summary-unit">%</div>
        </div>
    </div>

    <!-- 우선순위별 탭 -->
    <div class="priority-tabs">
        <button class="priority-tab active" onclick="filterRecommendations('all')">
            전체 (<span id="allCount">0</span>)
        </button>
        <button class="priority-tab" onclick="filterRecommendations('high')">
            🔴 높음 (<span id="highCount">0</span>)
        </button>
        <button class="priority-tab" onclick="filterRecommendations('medium')">
            🟡 중간 (<span id="mediumCount">0</span>)
        </button>
        <button class="priority-tab" onclick="filterRecommendations('low')">
            🟢 낮음 (<span id="lowCount">0</span>)
        </button>
    </div>

    <!-- 추천 테이블 -->
    <div class="table-wrapper">
        <table id="recommendationTable">
            <thead>
                <tr>
                    <th>
                        <input type="checkbox" id="selectAllRec" onchange="toggleSelectAll()">
                    </th>
                    <th>우선순위</th>
                    <th>키워드</th>
                    <th>제외 사유</th>
                    <th>광고비</th>
                    <th>매출</th>
                    <th>ROAS</th>
                    <th>낭비비용</th>
                    <th>클릭수</th>
                    <th>CTR</th>
                </tr>
            </thead>
            <tbody id="recommendationTableBody">
                <!-- 동적 생성 -->
            </tbody>
        </table>
    </div>
</div>
```

**추가할 JavaScript 함수:**
```javascript
// 추천 가져오기
async function getRecommendations() {
    if (!globalData || globalData.length === 0) {
        alert('먼저 데이터를 업로드하세요.');
        return;
    }

    try {
        const response = await fetch('/api/ad-analysis/coupang-recommendations', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'same-origin',
            body: JSON.stringify({
                data: globalData,
                criteria: {
                    min_roas: 50,
                    max_cpc: 1000,
                    min_ctr: 0.5
                }
            })
        });

        const result = await response.json();

        if (result.success) {
            window.recommendations = result.recommendations;
            displayRecommendations(result.recommendations, result.summary);
            document.getElementById('recommendationSection').style.display = 'block';
        }
    } catch (error) {
        console.error('Error fetching recommendations:', error);
        alert('추천 가져오기 실패');
    }
}

// 추천 표시
function displayRecommendations(recommendations, summary) {
    // 요약 카드
    document.getElementById('recWaste').textContent = formatNumber(summary.total_waste);
    document.getElementById('recCount').textContent = summary.keywords_to_exclude;
    document.getElementById('recSavings').textContent = summary.potential_savings.replace('%', '');

    // 우선순위별 카운트
    document.getElementById('allCount').textContent = recommendations.length;
    document.getElementById('highCount').textContent = summary.high_priority;
    document.getElementById('mediumCount').textContent = summary.medium_priority;
    document.getElementById('lowCount').textContent = summary.low_priority;

    // 테이블
    window.currentRecommendations = recommendations;
    renderRecommendationTable(recommendations);
}

function renderRecommendationTable(recommendations) {
    const tbody = document.getElementById('recommendationTableBody');

    tbody.innerHTML = recommendations.map((rec, idx) => {
        const priorityBadge = {
            'high': '<span class="priority-badge priority-high">🔴 높음</span>',
            'medium': '<span class="priority-badge priority-medium">🟡 중간</span>',
            'low': '<span class="priority-badge priority-low">🟢 낮음</span>'
        }[rec.priority];

        return `
            <tr>
                <td>
                    <input type="checkbox" class="rec-checkbox" data-keyword="${rec.keyword}">
                </td>
                <td>${priorityBadge}</td>
                <td><strong>${rec.keyword}</strong></td>
                <td>${rec.reason}</td>
                <td>${formatNumber(rec.spend)}원</td>
                <td>${formatNumber(rec.revenue)}원</td>
                <td>${rec.roas.toFixed(1)}%</td>
                <td class="text-danger"><strong>${formatNumber(rec.waste)}원</strong></td>
                <td>${formatNumber(rec.clicks)}</td>
                <td>${rec.ctr.toFixed(2)}%</td>
            </tr>
        `;
    }).join('');
}

// 우선순위 필터링
function filterRecommendations(priority) {
    if (!window.recommendations) return;

    let filtered;
    if (priority === 'all') {
        filtered = window.recommendations;
    } else {
        filtered = window.recommendations.filter(r => r.priority === priority);
    }

    renderRecommendationTable(filtered);

    // 탭 활성화
    document.querySelectorAll('.priority-tab').forEach(tab => {
        tab.classList.remove('active');
    });
    event.target.classList.add('active');
}

// 전체 선택/해제
function toggleSelectAll() {
    const checked = document.getElementById('selectAllRec').checked;
    document.querySelectorAll('.rec-checkbox').forEach(cb => {
        cb.checked = checked;
    });
}

// 추천 목록 다운로드
function exportRecommendations() {
    if (!window.recommendations || window.recommendations.length === 0) {
        alert('다운로드할 추천이 없습니다.');
        return;
    }

    const exportData = window.recommendations.map(rec => ({
        '우선순위': rec.priority === 'high' ? '높음' : (rec.priority === 'medium' ? '중간' : '낮음'),
        '키워드': rec.keyword,
        '제외 사유': rec.reason,
        '광고비': rec.spend,
        '매출': rec.revenue,
        'ROAS(%)': rec.roas.toFixed(2),
        '낭비비용': rec.waste,
        '클릭수': rec.clicks,
        'CTR(%)': rec.ctr.toFixed(2)
    }));

    const ws = XLSX.utils.json_to_sheet(exportData);
    const wb = XLSX.utils.book_new();
    XLSX.utils.book_append_sheet(wb, ws, "제외추천키워드");

    const today = new Date().toISOString().slice(0, 10);
    XLSX.writeFile(wb, `쿠팡_제외추천키워드_${today}.xlsx`);
}

// 선택 키워드 제외
function applyExclusions() {
    const selected = [];
    document.querySelectorAll('.rec-checkbox:checked').forEach(cb => {
        selected.push(cb.dataset.keyword);
    });

    if (selected.length === 0) {
        alert('제외할 키워드를 선택하세요.');
        return;
    }

    if (!confirm(`${selected.length}개 키워드를 제외하시겠습니까?\n\n제외된 키워드는 데이터에서 필터링됩니다.`)) {
        return;
    }

    // 전역 데이터에서 제외
    globalData = globalData.filter(row => !selected.includes(row.키워드));
    filteredData = [...globalData];

    // 재계산 및 표시
    const summary = calculateSummary(globalData);
    displaySummary(summary);
    displayKeywordTable(filteredData);
    displayCharts(filteredData);

    // 추천 재생성
    getRecommendations();

    alert(`✅ ${selected.length}개 키워드가 제외되었습니다.`);
}
```

**추가할 CSS:**
```css
/* 추천 섹션 */
.recommendation-summary {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 16px;
    margin-bottom: 24px;
}

.priority-tabs {
    display: flex;
    gap: 8px;
    margin-bottom: 16px;
    border-bottom: 2px solid var(--border-color);
}

.priority-tab {
    padding: 12px 20px;
    background: transparent;
    border: none;
    border-bottom: 3px solid transparent;
    cursor: pointer;
    font-size: 14px;
    font-weight: 500;
    color: var(--text-secondary);
    transition: all 0.3s;
}

.priority-tab.active {
    color: var(--primary);
    border-bottom-color: var(--primary);
}

.priority-tab:hover {
    color: var(--primary);
    background: var(--bg-hover);
}

.priority-badge {
    padding: 4px 12px;
    border-radius: 12px;
    font-size: 12px;
    font-weight: 600;
}

.priority-high {
    background: #fee;
    color: #c00;
}

.priority-medium {
    background: #ffeaa7;
    color: #d63031;
}

.priority-low {
    background: #dfe6e9;
    color: #636e72;
}

.text-danger {
    color: #ea4335;
}

.rec-checkbox {
    cursor: pointer;
    width: 18px;
    height: 18px;
}
```

---

### Phase 3: 차트 수정

#### 3.1 ROAS 바 차트 수정 (TOP 10만)

**파일:** `app/templates/ad_dashboard_coupang.html`

**수정 전 (line 813-820):**
```javascript
const sorted = [...data].sort((a, b) => (b.ROAS || 0) - (a.ROAS || 0));

// TOP 10 + BOTTOM 10
const top10 = sorted.slice(0, 10);
const bottom10 = sorted.slice(-10);
const chartData = [...top10, ...bottom10];
```

**수정 후:**
```javascript
const sorted = [...data].sort((a, b) => (b.ROAS || 0) - (a.ROAS || 0));

// TOP 10만
const chartData = sorted.slice(0, 10);
```

**차트 제목 변경:**
```javascript
plugins: {
    title: {
        display: true,
        text: 'ROAS 상위 TOP 10 키워드'  // 변경
    }
}
```

#### 3.2 산점도 차트 디버깅

**디버깅 코드 추가:**
```javascript
function displayScatterChart(data) {
    console.log('Scatter chart data:', data.length);

    if (data.length === 0) {
        console.warn('No data for scatter chart');
        return;
    }

    const ctx = document.getElementById('scatterChart');
    if (!ctx) {
        console.error('Scatter chart canvas not found');
        return;
    }

    const context = ctx.getContext('2d');

    // 기존 차트 파괴
    if (window.scatterChart) {
        window.scatterChart.destroy();
    }

    // 데이터 포인트 생성
    const points = data
        .filter(d => d.광고비 > 0 || d['총 전환매출액(1일)'] > 0)
        .map(d => ({
            x: d.광고비 || 0,
            y: d['총 전환매출액(1일)'] || 0,
            keyword: d.키워드
        }));

    console.log('Scatter points:', points.length);

    if (points.length === 0) {
        // 빈 차트 표시
        ctx.parentElement.innerHTML = '<p style="text-align:center; padding:40px; color:#999;">데이터가 부족합니다</p>';
        return;
    }

    window.scatterChart = new Chart(context, {
        type: 'scatter',
        data: {
            datasets: [{
                label: '키워드',
                data: points,
                backgroundColor: 'rgba(26, 115, 232, 0.5)',
                borderColor: 'rgba(26, 115, 232, 1)',
                pointRadius: 6,
                pointHoverRadius: 8
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                title: {
                    display: true,
                    text: '광고비 vs 매출액 분포'
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const point = context.raw;
                            return [
                                `키워드: ${point.keyword}`,
                                `광고비: ${formatNumber(point.x)}원`,
                                `매출: ${formatNumber(point.y)}원`
                            ];
                        }
                    }
                }
            },
            scales: {
                x: {
                    title: { display: true, text: '광고비 (원)' },
                    beginAtZero: true,
                    ticks: {
                        callback: function(value) {
                            return formatNumber(value);
                        }
                    }
                },
                y: {
                    title: { display: true, text: '매출액 (원)' },
                    beginAtZero: true,
                    ticks: {
                        callback: function(value) {
                            return formatNumber(value);
                        }
                    }
                }
            }
        }
    });
}
```

---

### Phase 4: UI 개선

#### 4.1 추천 버튼 추가

**파일:** `app/templates/ad_dashboard_coupang.html`

**업로드 섹션 하단에 추가 (line 370 이후):**
```html
<div class="action-buttons" style="margin-top: 20px; text-align: center;">
    <button class="btn btn-primary" onclick="getRecommendations()">
        🎯 제외 키워드 추천받기
    </button>
</div>
```

#### 4.2 데이터 업로드 시 자동 추천

**JavaScript 수정:**
```javascript
async function handleFileUpload(file) {
    // ... 기존 코드 ...

    if (result.success) {
        // ... 기존 표시 로직 ...

        // 자동 추천 (사용자에게 묻기)
        if (confirm('키워드 제외 추천을 받으시겠습니까?')) {
            await getRecommendations();
        }
    }
}
```

---

## 📋 구현 순서

### 우선순위 1: 데이터 정확성 (즉시)
1. ✅ `ad_analysis.py` 백엔드 필터링 수정
2. ✅ 테스트 실행하여 메트릭스 확인
3. ✅ ROAS 차트 TOP 10으로 변경

### 우선순위 2: 산점도 차트 수정 (즉시)
1. ✅ 디버깅 코드 추가
2. ✅ 데이터 포인트 필터링 개선
3. ✅ 빈 데이터 처리

### 우선순위 3: 키워드 추천 시스템 (중요)
1. ✅ 백엔드 API 구현
2. ✅ 프론트엔드 섹션 추가
3. ✅ 테이블 및 필터 구현
4. ✅ Excel 다운로드 기능

### 우선순위 4: UI/UX 개선 (부가)
1. ✅ 추천 버튼 추가
2. ✅ 자동 추천 옵션
3. ✅ 스타일링 개선

---

## 🧪 테스트 계획

### 테스트 1: 데이터 필터링
```python
# test_coupang_filtering.py
import pandas as pd

df = pd.read_excel('골덴바지(자동광고).xlsx')

# 필터링 전
print('필터링 전:', len(df), '행')
print('광고비:', df['광고비'].sum())

# 필터링 후
df = df[df['광고 노출 지면'] == '검색 영역']
df = df[df['키워드'] != '-']

print('필터링 후:', len(df), '행')
print('광고비:', df['광고비'].sum())  # 예상: 41,942원
print('매출:', df['총 전환매출액(1일)'].sum())  # 예상: 144,000원
print('ROAS:', df['총 전환매출액(1일)'].sum() / df['광고비'].sum() * 100)  # 예상: 343.33%
```

### 테스트 2: 추천 시스템
```python
# test_recommendations.py
# 추천 API 호출 후 결과 검증
# - 전환 없는 키워드 182개 탐지되는지
# - 우선순위 분류 정확한지
# - 낭비 광고비 계산 정확한지
```

### 테스트 3: E2E 테스트
```python
# test_coupang_e2e.py (Playwright)
# 1. 파일 업로드
# 2. 메트릭스 확인 (41,942원, 144,000원, 343.33%)
# 3. 추천 버튼 클릭
# 4. 추천 섹션 표시 확인
# 5. 키워드 제외 적용
# 6. 재계산 확인
```

---

## 📊 예상 결과

### 수정 후 메트릭스
```
총광고비: 41,942원 (현재: 242,795원)
총매출액: 144,000원 (현재: 567,660원)
평균ROAS: 343.33% (현재: 199.63%)
키워드 수: 190개 (현재: 229개)
```

### 추천 시스템 결과
```
제외 추천 키워드: 182개
낭비 광고비: 39,447원
절감 가능 비율: 94%

우선순위별:
- 높음 (전환 없음): 182개
- 중간 (ROAS 50% 이하): 0개
- 낮음 (CPC/CTR 문제): 약 10개
```

---

## 🎯 최종 목표

**사용자 요구사항 달성:**
1. ✅ 정확한 메트릭스 (비검색영역 제외)
2. ✅ ROAS TOP 10 표시
3. ✅ 산점도 차트 표시
4. ✅ 키워드 제외 추천 시스템
5. ✅ 추천 결과 별도 표시

**추가 가치:**
- 94% 광고비 낭비 발견
- 데이터 기반 키워드 최적화
- Excel 다운로드로 실무 활용
- 우선순위별 단계적 제외 가능

---

## 💡 다음 단계 (선택사항)

1. **AI 추천 고도화**
   - GPT-4로 키워드 조합 분석
   - 유사 키워드 그룹핑
   - 계절성/트렌드 분석

2. **자동화**
   - 주간 자동 리포트
   - 슬랙/이메일 알림
   - 임계값 초과 시 자동 알림

3. **A/B 테스트**
   - 제외 전/후 성과 비교
   - ROI 측정

---

**구현 시작하시겠습니까?**
