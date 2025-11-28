# 디자인 시스템

## 디자인 철학

**깔끔하고 세련된 데이터 대시보드**
- 직관적인 정보 계층 구조
- 부드러운 그라디언트와 그림자
- 명확한 시각적 피드백
- 초보자도 쉽게 이해할 수 있는 레이아웃
- 데이터에 집중할 수 있는 미니멀한 디자인

---

## 색상 팔레트

### Primary Colors (메인 색상)
```css
/* 보라-파랑 그라디언트 */
--primary-start: #667eea;  /* 밝은 보라 */
--primary-end: #764ba2;    /* 진한 보라 */
--primary-gradient: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
```
![Primary Gradient](https://via.placeholder.com/200x80/667eea/ffffff?text=Primary+Gradient)

**사용처**: 메인 버튼, 강조 영역, 메트릭 카드

### Success (성공/우수)
```css
--success: #2ecc71;        /* 밝은 녹색 */
--success-light: #d4edda;  /* 연한 녹색 배경 */
--success-dark: #155724;   /* 진한 녹색 텍스트 */
--success-gradient: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
```
![Success](https://via.placeholder.com/200x80/2ecc71/ffffff?text=Success)

**사용처**: 우수 성과 지표, 긍정적 트렌드, 성공 알림

### Warning (주의)
```css
--warning: #f39c12;        /* 주황색 */
--warning-light: #fff3cd;
--warning-dark: #856404;
--warning-gradient: linear-gradient(135deg, #fa709a 0%, #fee140 100%);
```
![Warning](https://via.placeholder.com/200x80/f39c12/ffffff?text=Warning)

**사용처**: 주의 필요 지표, 예산 주의 상태

### Danger (위험/문제)
```css
--danger: #e74c3c;         /* 빨간색 */
--danger-light: #f8d7da;
--danger-dark: #721c24;
```
![Danger](https://via.placeholder.com/200x80/e74c3c/ffffff?text=Danger)

**사용처**: 위험 상태, 삭제 버튼, 에러 메시지

### Info (정보)
```css
--info: #3498db;           /* 밝은 파랑 */
--info-gradient: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
```
![Info](https://via.placeholder.com/200x80/3498db/ffffff?text=Info)

**사용처**: 정보성 지표, 링크, AI 인사이트 강조

### Neutral (중립/배경)
```css
--bg-primary: #f5f7fa;     /* 페이지 배경 */
--bg-secondary: #ffffff;   /* 카드 배경 */
--bg-tertiary: #f8f9fa;    /* 섹션 배경 */

--text-primary: #2c3e50;   /* 메인 텍스트 */
--text-secondary: #7f8c8d; /* 보조 텍스트 */
--text-disabled: #95a5a6;  /* 비활성 텍스트 */

--border-light: #ecf0f1;   /* 연한 테두리 */
--border-medium: #bdc3c7;  /* 중간 테두리 */
--border-dark: #95a5a6;    /* 진한 테두리 */
```

---

## 타이포그래피

### 폰트 패밀리
```css
font-family: 'Noto Sans KR', -apple-system, BlinkMacSystemFont,
             'Segoe UI', 'Roboto', 'Helvetica Neue', Arial, sans-serif;
```

**한글 지원**: Noto Sans KR (Google Fonts CDN)
```html
<link href="https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@300;400;500;600;700&display=swap" rel="stylesheet">
```

### 폰트 크기
| 용도 | 크기 | 무게 | 예시 |
|------|------|------|------|
| H1 (페이지 제목) | 28px | 700 (Bold) | 광고 분석 대시보드 |
| H2 (섹션 제목) | 20px | 600 (Semibold) | 주요 지표 |
| H3 (카드 제목) | 16px | 600 | 캠페인별 성과 |
| Body (본문) | 14px | 400 (Regular) | 일반 텍스트 |
| Small (보조) | 12px | 400 | 날짜, 부가 정보 |
| Metric Value (지표 값) | 32px | 700 | 3.5, 1,200만원 |

### 줄 간격
```css
--line-height-tight: 1.2;   /* 제목 */
--line-height-normal: 1.5;  /* 본문 */
--line-height-relaxed: 1.6; /* AI 인사이트, 긴 텍스트 */
```

---

## 간격 시스템 (Spacing)

### 8px 기반 그리드
```css
--space-xs: 4px;    /* 0.5 × 8 */
--space-sm: 8px;    /* 1 × 8 */
--space-md: 16px;   /* 2 × 8 */
--space-lg: 24px;   /* 3 × 8 */
--space-xl: 32px;   /* 4 × 8 */
--space-2xl: 48px;  /* 6 × 8 */
--space-3xl: 64px;  /* 8 × 8 */
```

**사용 가이드**:
- 컴포넌트 내부 padding: `--space-md` (16px)
- 컴포넌트 간 margin: `--space-lg` (24px)
- 섹션 간 margin: `--space-xl` (32px)
- 페이지 여백: `--space-lg` (24px)

---

## 레이아웃

### 컨테이너
```css
.container {
    max-width: 1400px;
    margin: 0 auto;
    padding: 20px;
}
```

### 그리드 시스템
```css
/* 메트릭 카드 그리드 */
.metrics-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 20px;
}

/* 차트 그리드 (2:1 비율) */
.charts-grid {
    display: grid;
    grid-template-columns: 2fr 1fr;
    gap: 20px;
}
```

### 반응형 브레이크포인트
```css
/* Mobile */
@media (max-width: 767px) {
    .metrics-grid {
        grid-template-columns: 1fr;
    }
    .charts-grid {
        grid-template-columns: 1fr;
    }
}

/* Tablet */
@media (min-width: 768px) and (max-width: 1024px) {
    .metrics-grid {
        grid-template-columns: repeat(2, 1fr);
    }
}

/* Desktop */
@media (min-width: 1025px) {
    .metrics-grid {
        grid-template-columns: repeat(3, 1fr);
    }
}
```

---

## 컴포넌트

### 1. 메트릭 카드 (Metric Card)

**디자인 특징**:
- 그라디언트 배경
- 흰색 텍스트
- 큰 숫자 (32px, Bold)
- 부드러운 그림자
- 호버 시 약간 위로 떠오르는 효과

```css
.metric-card {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    border-radius: 16px;
    padding: 24px;
    color: white;
    box-shadow: 0 8px 16px rgba(0, 0, 0, 0.1);
    transition: transform 0.3s ease, box-shadow 0.3s ease;
}

.metric-card:hover {
    transform: translateY(-4px);
    box-shadow: 0 12px 24px rgba(0, 0, 0, 0.15);
}

.metric-label {
    font-size: 14px;
    opacity: 0.9;
    margin-bottom: 8px;
}

.metric-value {
    font-size: 32px;
    font-weight: 700;
    line-height: 1.2;
}

.metric-change {
    font-size: 12px;
    margin-top: 8px;
    opacity: 0.8;
}
```

**색상 변형**:
```css
.metric-card.green {
    background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
}

.metric-card.blue {
    background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
}

.metric-card.orange {
    background: linear-gradient(135deg, #fa709a 0%, #fee140 100%);
}
```

### 2. 버튼 (Button)

**기본 스타일**:
```css
.btn {
    padding: 10px 20px;
    border: none;
    border-radius: 8px;
    cursor: pointer;
    font-size: 14px;
    font-weight: 500;
    transition: all 0.3s ease;
    display: inline-flex;
    align-items: center;
    gap: 8px;
}

.btn-primary {
    background: #3498db;
    color: white;
}

.btn-primary:hover {
    background: #2980b9;
    transform: translateY(-2px);
    box-shadow: 0 4px 8px rgba(52, 152, 219, 0.3);
}

.btn-success {
    background: #2ecc71;
    color: white;
}

.btn-danger {
    background: #e74c3c;
    color: white;
}

.btn-secondary {
    background: #95a5a6;
    color: white;
}
```

### 3. 업로드 영역 (Upload Area)

```css
.upload-area {
    border: 2px dashed #bdc3c7;
    border-radius: 12px;
    padding: 40px;
    text-align: center;
    background: #f8f9fa;
    cursor: pointer;
    transition: all 0.3s ease;
}

.upload-area:hover {
    border-color: #3498db;
    background: #e3f2fd;
}

.upload-area.dragging {
    border-color: #2ecc71;
    background: #d5f4e6;
    transform: scale(1.02);
}
```

### 4. 테이블 (Table)

```css
table {
    width: 100%;
    border-collapse: collapse;
    background: white;
}

th {
    background: #f8f9fa;
    padding: 12px 16px;
    text-align: left;
    font-weight: 600;
    color: #7f8c8d;
    font-size: 13px;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}

td {
    padding: 12px 16px;
    border-bottom: 1px solid #ecf0f1;
    font-size: 14px;
    color: #2c3e50;
}

tr:hover {
    background: #f8f9fa;
}

tr:last-child td {
    border-bottom: none;
}
```

### 5. 상태 배지 (Status Badge)

```css
.status-badge {
    display: inline-block;
    padding: 4px 12px;
    border-radius: 12px;
    font-size: 12px;
    font-weight: 600;
}

.status-excellent {
    background: #d4edda;
    color: #155724;
}

.status-good {
    background: #fff3cd;
    color: #856404;
}

.status-poor {
    background: #f8d7da;
    color: #721c24;
}
```

### 6. 모달 (Modal)

```css
.modal {
    display: none; /* JavaScript로 제어 */
    position: fixed;
    z-index: 1000;
    left: 0;
    top: 0;
    width: 100%;
    height: 100%;
    background: rgba(0, 0, 0, 0.5);
    backdrop-filter: blur(4px);
}

.modal-content {
    background: white;
    margin: 10% auto;
    padding: 30px;
    border-radius: 16px;
    width: 90%;
    max-width: 500px;
    box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
    animation: modalFadeIn 0.3s ease;
}

@keyframes modalFadeIn {
    from {
        opacity: 0;
        transform: translateY(-20px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
}
```

### 7. AI 인사이트 박스

```css
.insights-box {
    background: #f8f9fa;
    border-left: 4px solid #3498db;
    padding: 20px;
    border-radius: 8px;
    white-space: pre-wrap;
    line-height: 1.6;
    font-size: 14px;
    color: #2c3e50;
}

.insights-box h3 {
    color: #3498db;
    margin-bottom: 12px;
}

.insights-box strong {
    color: #2c3e50;
    font-weight: 600;
}
```

---

## 아이콘 시스템

### Unicode/Emoji 사용
```html
<!-- 섹션 제목 -->
📊 주요 지표
📈 일별 트렌드
💡 AI 인사이트
🏆 캠페인별 성과
🎯 월별 목표

<!-- 버튼 -->
📤 업로드
💾 저장
📄 PDF
📊 Excel
📥 템플릿 다운로드

<!-- 상태 -->
✅ 정상
⚠️ 주의
❌ 위험
```

---

## 애니메이션

### 페이드 인
```css
@keyframes fadeIn {
    from {
        opacity: 0;
        transform: translateY(20px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
}

.fade-in {
    animation: fadeIn 0.5s ease;
}
```

### 로딩 스피너
```css
.spinner {
    border: 4px solid #f3f3f3;
    border-top: 4px solid #3498db;
    border-radius: 50%;
    width: 40px;
    height: 40px;
    animation: spin 1s linear infinite;
}

@keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
}
```

---

## 차트 스타일 (Chart.js)

### 색상 팔레트
```javascript
const chartColors = {
    roas: 'rgb(46, 204, 113)',      // 녹색
    ctr: 'rgb(52, 152, 219)',       // 파랑
    spend: 'rgb(155, 89, 182)',     // 보라
    revenue: 'rgb(241, 196, 15)',   // 노랑
    conversions: 'rgb(230, 126, 34)' // 주황
};
```

### 차트 옵션
```javascript
const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
        legend: {
            position: 'top',
            labels: {
                font: {
                    family: "'Noto Sans KR', sans-serif",
                    size: 12
                },
                padding: 15,
                usePointStyle: true
            }
        },
        tooltip: {
            backgroundColor: 'rgba(44, 62, 80, 0.9)',
            titleFont: {
                family: "'Noto Sans KR', sans-serif",
                size: 14
            },
            bodyFont: {
                family: "'Noto Sans KR', sans-serif",
                size: 13
            },
            padding: 12,
            cornerRadius: 8
        }
    }
};
```

---

## 다크 모드 (추후 확장)

```css
@media (prefers-color-scheme: dark) {
    :root {
        --bg-primary: #1a1a1a;
        --bg-secondary: #2c2c2c;
        --text-primary: #ffffff;
        --text-secondary: #b0b0b0;
        --border-light: #404040;
    }
}
```

---

## 접근성 (Accessibility)

### 색상 대비
- 텍스트/배경 대비율: 최소 4.5:1 (WCAG AA)
- 대형 텍스트(18px+): 최소 3:1

### 포커스 상태
```css
*:focus {
    outline: 2px solid #3498db;
    outline-offset: 2px;
}

button:focus-visible {
    box-shadow: 0 0 0 3px rgba(52, 152, 219, 0.3);
}
```

### 키보드 내비게이션
- 모든 인터랙티브 요소는 Tab으로 접근 가능
- Enter/Space로 버튼 활성화

---

## 사용 예시

### 메트릭 카드 HTML
```html
<div class="metric-card green">
    <div class="metric-label">ROAS</div>
    <div class="metric-value">3.5</div>
    <div class="metric-change">▲ 8.6% vs 이전 기간</div>
</div>
```

### 버튼 HTML
```html
<button class="btn btn-primary">
    💾 분석 저장
</button>
```

### 상태 배지 HTML
```html
<span class="status-badge status-excellent">우수</span>
<span class="status-badge status-good">보통</span>
<span class="status-badge status-poor">개선필요</span>
```

---

## 참고 자료

- [Material Design Color Tool](https://material.io/resources/color/)
- [Coolors Palette Generator](https://coolors.co/)
- [Chart.js Documentation](https://www.chartjs.org/docs/latest/)
- [WCAG 2.1 Guidelines](https://www.w3.org/WAI/WCAG21/quickref/)
