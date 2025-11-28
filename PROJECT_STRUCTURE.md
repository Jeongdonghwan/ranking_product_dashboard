# 📁 프로젝트 구조

**광고 분석 대시보드 - 완전한 파일 구조**

---

## 🌳 디렉토리 트리

```
insight/
│
├── 📂 app/                           # 애플리케이션 메인 디렉토리
│   ├── __init__.py                   # Flask 앱 팩토리 (200 lines)
│   │
│   ├── 📂 routes/                    # API 엔드포인트
│   │   ├── __init__.py
│   │   └── ad_analysis.py            # 17개 API 엔드포인트 (800 lines)
│   │
│   ├── 📂 services/                  # 비즈니스 로직
│   │   ├── __init__.py
│   │   ├── ad_analyzer.py            # 분석 엔진 (600 lines)
│   │   └── ai_insights.py            # AI 인사이트 생성 (300 lines)
│   │
│   ├── 📂 utils/                     # 유틸리티 함수
│   │   ├── __init__.py
│   │   ├── db_utils.py               # 데이터베이스 유틸 (450 lines)
│   │   ├── auth_utils.py             # 인증 유틸 (350 lines)
│   │   └── helpers.py                # 헬퍼 함수 (400 lines)
│   │
│   ├── 📂 templates/                 # HTML 템플릿
│   │   ├── ad_dashboard.html         # 대시보드 (700 lines)
│   │   ├── error.html                # 에러 페이지
│   │   └── login.html                # 로그인 페이지
│   │
│   └── 📂 static/                    # 정적 파일
│       ├── 📂 js/
│       │   └── ad_dashboard.js       # JavaScript 로직 (600 lines)
│       ├── 📂 css/
│       └── 📂 templates/
│           └── TEMPLATE_GUIDE.md     # 템플릿 가이드 (216 lines)
│
├── 📂 config/                        # 설정 파일
│   ├── __init__.py
│   └── settings.py                   # Flask 설정 클래스 (150 lines)
│
├── 📂 database/                      # 데이터베이스 스키마
│   └── schema.sql                    # 테이블 정의 (206 lines)
│
├── 📂 docs/                          # 추가 문서 (선택)
│   ├── ARCHITECTURE.md
│   ├── API_SPEC.md
│   ├── DATABASE_DESIGN.md
│   └── DESIGN_SYSTEM.md
│
├── 📂 logs/                          # 로그 파일 (자동 생성)
│   └── app.log
│
├── 📂 uploads/                       # 업로드 파일 (자동 생성)
│
├── 📂 flask_session/                 # 세션 파일 (자동 생성)
│
├── 📄 run.py                         # 앱 실행 스크립트 (50 lines)
├── 📄 requirements.txt               # Python 패키지 목록
├── 📄 .env.example                   # 환경변수 예제
├── 📄 .gitignore                     # Git 제외 파일
│
├── 📄 README.md                      # 프로젝트 개요 (263 lines)
├── 📄 CLAUDE.md                      # 구현 가이드 (2,391 lines)
├── 📄 IMPLEMENTATION_STATUS.md       # 구현 상태
├── 📄 DEPLOYMENT_GUIDE.md            # 배포 가이드 (604 lines)
├── 📄 PROJECT_COMPLETE.md            # 완료 보고서
├── 📄 QUICK_START.md                 # 빠른 시작 가이드
├── 📄 VERIFICATION_CHECKLIST.md      # 검증 체크리스트
└── 📄 PROJECT_STRUCTURE.md           # 이 파일
```

---

## 📊 파일 통계

| 카테고리 | 파일 수 | 총 라인 수 | 설명 |
|---------|--------|----------|------|
| **Backend 코어** | 10 | ~3,500 | 유틸, 서비스, 라우트 |
| **Frontend** | 4 | ~1,300 | HTML, JavaScript |
| **설정** | 5 | ~500 | Flask 설정, 환경변수 |
| **데이터베이스** | 1 | 206 | SQL 스키마 |
| **문서** | 7 | ~5,200 | 가이드, 매뉴얼 |
| **총계** | **27** | **~10,700** | - |

---

## 🔍 주요 파일 상세

### Backend 코어

#### `app/__init__.py` (200 lines)
- Flask 앱 팩토리 패턴
- Blueprint 등록
- 에러 핸들러 설정
- 로깅 초기화

**핵심 함수:**
```python
def create_app(config_name='development')
def init_database()
def register_blueprints(app)
def register_error_handlers(app)
```

---

#### `app/routes/ad_analysis.py` (800 lines)
- 17개 API 엔드포인트
- RESTful 설계
- 인증 데코레이터 적용
- JSON 응답

**엔드포인트 목록:**
```
인증 (4개):
  GET  /
  GET  /ad-dashboard
  GET  /login
  GET  /logout

데이터 입력 (2개):
  POST /api/ad-analysis/upload
  POST /api/ad-analysis/manual-input

분석 관리 (4개):
  GET    /api/ad-analysis/snapshots
  GET    /api/ad-analysis/snapshots/:id
  PUT    /api/ad-analysis/snapshots/:id
  DELETE /api/ad-analysis/snapshots/:id

분석 기능 (5개):
  GET  /api/ad-analysis/compare
  GET  /api/ad-analysis/budget-pacing
  GET  /api/ad-analysis/goals
  POST /api/ad-analysis/goals
  GET/POST /api/ad-analysis/memos

리포트 (3개):
  GET /api/ad-analysis/export/pdf/:id
  GET /api/ad-analysis/export/excel/:id
  GET /api/ad-analysis/template/:type
```

---

#### `app/services/ad_analyzer.py` (600 lines)
- 핵심 분석 로직
- pandas 기반 데이터 처리
- 지표 계산 알고리즘

**핵심 클래스:**
```python
class AdAnalyzer:
    def save_snapshot(df, snapshot_name)
    def calculate_metrics(snapshot_id)
    def _calculate_campaign_metrics(df)
    def _calculate_daily_trend(df)
    def compare_snapshots(snapshot_a, snapshot_b)
    def calculate_budget_pacing(year_month)
    def check_ownership(snapshot_id)
```

**계산 지표:**
- ROAS (Return on Ad Spend)
- CTR (Click-Through Rate)
- CPA (Cost Per Acquisition)
- CVR (Conversion Rate)
- CPC (Cost Per Click)
- AOV (Average Order Value)

---

#### `app/services/ai_insights.py` (300 lines)
- OpenAI GPT-4 연동
- 프롬프트 엔지니어링
- Fallback 로직

**핵심 클래스:**
```python
class AIInsights:
    def generate_insights(metrics, df)
    def _create_prompt(metrics, df)
    def _generate_fallback_insights(metrics)
```

**생성 콘텐츠:**
- 3줄 요약
- 주요 발견사항
- 우선순위별 액션 아이템
- 예산 재배분 제안

---

#### `app/utils/db_utils.py` (450 lines)
- 데이터베이스 연결 관리
- Context manager 패턴
- 트랜잭션 관리

**핵심 함수:**
```python
def get_db_connection()
def get_db_cursor(commit=False)
def execute_query(sql, params)
def execute_insert(sql, params)
def execute_update(sql, params)
def execute_delete(sql, params)
def execute_many(sql, params_list)
def init_database()
```

---

#### `app/utils/auth_utils.py` (350 lines)
- JWT 토큰 검증
- 세션 관리
- 데코레이터 패턴

**핵심 함수:**
```python
def verify_jwt_token(token)
def create_session(user_id, user_data)
def get_current_user()
def require_auth(f)
def optional_auth(f)
def check_resource_ownership(resource_type, resource_id)
```

---

#### `app/utils/helpers.py` (400 lines)
- 파일 처리
- 포맷팅 함수
- 지표 계산

**핵심 함수:**
```python
# 파일 처리
def allowed_file(filename)
def clean_filename(filename)
def sanitize_path(path)

# 포맷팅
def format_currency(value)
def format_percentage(value)
def format_number(value)
def format_date(date)

# 지표 계산
def calculate_roas(revenue, spend)
def calculate_ctr(clicks, impressions)
def calculate_cpa(spend, conversions)
def calculate_cvr(conversions, clicks)
def calculate_cpc(spend, clicks)

# 응답 헬퍼
def success_response(data)
def error_response(message, status_code)
```

---

### Frontend

#### `app/templates/ad_dashboard.html` (700 lines)
- 단일 페이지 애플리케이션 (SPA)
- 5개 탭 구조
- 반응형 디자인
- Chart.js 통합

**구조:**
```html
<header>
  <h1>📊 광고 분석 대시보드</h1>
  <div class="tabs">
    <!-- 5개 탭 -->
  </div>
</header>

<div id="tab-upload">
  <!-- 파일 업로드, 수기 입력 -->
</div>

<div id="tab-analysis">
  <!-- 메트릭 카드, 차트, 테이블 -->
</div>

<div id="tab-compare">
  <!-- 기간 비교 -->
</div>

<div id="tab-saved">
  <!-- 저장된 분석 목록 -->
</div>

<div id="tab-goals">
  <!-- 목표 관리, 예산 소진 -->
</div>

<!-- 모달: 저장, 수기 입력 -->
```

**CSS 특징:**
- CSS Grid & Flexbox
- 그라디언트 배경
- 호버 효과
- 반응형 브레이크포인트

---

#### `app/static/js/ad_dashboard.js` (600 lines)
- Vanilla JavaScript (프레임워크 없음)
- Fetch API 사용
- Chart.js 렌더링
- 이벤트 처리

**핵심 함수:**
```javascript
// 초기화
initTabs()
initUpload()
loadSnapshots()

// 파일 처리
uploadFile(file)
addManualData()
submitManualData()

// 데이터 표시
displayMetrics(metrics)
displayChart(dailyData)
displayCampaigns(campaigns)
displayInsights(insights)

// 분석 관리
saveCurrentAnalysis()
loadSnapshot(snapshotId)
deleteSnapshot(snapshotId)

// 비교 분석
compareAnalysis()

// 목표 관리
saveGoal()
loadBudgetPacing()

// 유틸리티
downloadTemplate(type)
exportPDF()
exportExcel()
```

---

### 데이터베이스

#### `database/schema.sql` (206 lines)
- 4개 테이블 정의
- 인덱스 최적화
- 외래 키 제약

**테이블 구조:**

```sql
1. ad_analysis_snapshots (분석 스냅샷)
   - id (PK)
   - user_id (FK → users)
   - snapshot_name
   - period_start, period_end
   - data_json (TEXT)
   - metrics_summary (JSON)
   - ai_insights (TEXT)
   - is_saved, tags, memo
   - created_at, updated_at

2. ad_daily_data (일별 데이터)
   - id (PK)
   - snapshot_id (FK → ad_analysis_snapshots)
   - date
   - campaign_name
   - spend, impressions, clicks, conversions, revenue

3. ad_campaign_memos (캠페인 메모)
   - id (PK)
   - user_id (FK → users)
   - campaign_name
   - memo
   - created_at

4. ad_monthly_goals (월별 목표)
   - id (PK)
   - user_id (FK → users)
   - year_month (YYYY-MM)
   - budget, target_roas, target_revenue
```

**인덱스:**
- `idx_user_date`: (user_id, period_start, period_end)
- `idx_saved`: (user_id, is_saved)
- `idx_snapshot_date`: (snapshot_id, date)
- `idx_campaign`: (campaign_name)
- `uk_user_month`: UNIQUE (user_id, year_month)

---

### 설정

#### `config/settings.py` (150 lines)
- Flask 설정 클래스
- 환경별 설정 (Development, Production, Testing)
- 환경변수 로드

**설정 클래스:**
```python
class Config:
    SECRET_KEY
    JWT_SECRET_KEY
    DATABASE_CONFIG
    SESSION_CONFIG
    UPLOAD_CONFIG
    LOGGING_CONFIG
    OPENAI_CONFIG

class DevelopmentConfig(Config):
    DEBUG = True

class ProductionConfig(Config):
    DEBUG = False

class TestingConfig(Config):
    TESTING = True
```

---

#### `.env.example`
- 환경변수 템플릿
- 필수 설정 항목
- 주석 포함

**주요 변수:**
```env
FLASK_ENV=development
SECRET_KEY=...
JWT_SECRET_KEY=...
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=...
OPENAI_API_KEY=...
```

---

#### `requirements.txt`
- Python 패키지 목록
- 버전 고정

**주요 패키지:**
```
Flask==3.0.0
PyMySQL==1.1.0
pandas==2.1.0
openpyxl==3.1.2
openai==1.3.0
PyJWT==2.8.0
```

---

## 🔄 데이터 흐름

### 1. 파일 업로드 플로우

```
사용자
  ↓ (파일 드래그)
ad_dashboard.js: uploadFile()
  ↓ (FormData POST)
ad_analysis.py: /api/ad-analysis/upload
  ↓ (pandas 파싱)
ad_analyzer.py: save_snapshot()
  ↓ (SQL INSERT)
database: ad_analysis_snapshots, ad_daily_data
  ↓
ad_analyzer.py: calculate_metrics()
  ↓ (지표 계산)
ai_insights.py: generate_insights()
  ↓ (OpenAI API)
ad_analysis.py: Response JSON
  ↓
ad_dashboard.js: displayMetrics(), displayChart()
  ↓
사용자 브라우저 (차트 표시)
```

---

### 2. 인증 플로우

```
mbizsquare.com
  ↓ (JWT 생성)
/?token=xxx
  ↓
ad_analysis.py: index()
  ↓
auth_utils.py: verify_jwt_token()
  ↓ (검증 성공)
auth_utils.py: create_session()
  ↓ (세션 생성)
Redirect → /ad-dashboard
  ↓
ad_analysis.py: dashboard()
  ↓ (@require_auth)
auth_utils.py: get_current_user()
  ↓
ad_dashboard.html 렌더링
```

---

### 3. 분석 비교 플로우

```
사용자
  ↓ (두 분석 선택)
ad_dashboard.js: compareAnalysis()
  ↓ (GET 요청)
ad_analysis.py: /api/ad-analysis/compare
  ↓
ad_analyzer.py: compare_snapshots()
  ↓ (SQL 조회)
database: metrics_summary 추출
  ↓ (변화율 계산)
ad_analyzer.py: _generate_comparison_summary()
  ↓ (JSON 응답)
ad_dashboard.js: 비교 테이블 렌더링
  ↓
사용자 브라우저 (비교 결과 표시)
```

---

## 🛠️ 개발 워크플로우

### 로컬 개발

1. **환경 설정**
   ```bash
   python -m venv venv
   venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **데이터베이스 설정**
   ```bash
   mysql -u root -p mbizsquare < database/schema.sql
   ```

3. **환경변수 설정**
   ```bash
   cp .env.example .env
   # .env 편집
   ```

4. **실행**
   ```bash
   python run.py
   ```

5. **접속**
   ```
   http://localhost:5000
   ```

---

### 프로덕션 배포

1. **서버 준비**
   - Ubuntu 20.04+
   - Python 3.8+
   - MariaDB 10.x+
   - Nginx

2. **코드 배포**
   ```bash
   git clone <repository>
   cd insight
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

3. **데이터베이스 배포**
   ```bash
   mysql -u root -p mbizsquare < database/schema.sql
   ```

4. **환경변수 설정**
   ```bash
   cp .env.example .env
   # FLASK_ENV=production 설정
   ```

5. **Gunicorn 실행**
   ```bash
   gunicorn -w 4 -b 0.0.0.0:5000 run:app
   ```

6. **Nginx 리버스 프록시**
   ```nginx
   server {
       listen 80;
       server_name insight.mbizsquare.com;

       location / {
           proxy_pass http://127.0.0.1:5000;
       }
   }
   ```

---

## 📚 문서 구조

| 문서 | 용도 | 대상 |
|------|------|------|
| **README.md** | 프로젝트 개요 | 모든 사용자 |
| **CLAUDE.md** | 구현 가이드 | 개발자 |
| **QUICK_START.md** | 빠른 시작 | 신규 사용자 |
| **DEPLOYMENT_GUIDE.md** | 배포 가이드 | 운영자 |
| **IMPLEMENTATION_STATUS.md** | 구현 상태 | 프로젝트 관리자 |
| **PROJECT_COMPLETE.md** | 완료 보고서 | 이해관계자 |
| **VERIFICATION_CHECKLIST.md** | 검증 체크리스트 | QA 팀 |
| **PROJECT_STRUCTURE.md** | 구조 설명 | 개발자 |
| **TEMPLATE_GUIDE.md** | 템플릿 가이드 | 최종 사용자 |

---

## 🔍 파일 찾기

### 기능별 파일 위치

**인증이 필요할 때:**
- `app/utils/auth_utils.py` 참조

**데이터베이스 쿼리:**
- `app/utils/db_utils.py` 참조

**분석 로직 수정:**
- `app/services/ad_analyzer.py` 참조

**AI 인사이트 수정:**
- `app/services/ai_insights.py` 참조

**API 엔드포인트 추가:**
- `app/routes/ad_analysis.py` 수정

**UI 수정:**
- `app/templates/ad_dashboard.html` (HTML)
- `app/static/js/ad_dashboard.js` (JavaScript)

**설정 변경:**
- `config/settings.py` (코드)
- `.env` (환경변수)

**데이터베이스 스키마 변경:**
- `database/schema.sql` 수정

---

## 📈 확장 가이드

### 새 API 엔드포인트 추가

1. `app/routes/ad_analysis.py`에 함수 추가
   ```python
   @ad_bp.route('/api/ad-analysis/new-feature', methods=['GET'])
   @require_auth
   def new_feature():
       # 로직 구현
       return success_response(data)
   ```

2. `app/static/js/ad_dashboard.js`에 클라이언트 함수 추가
   ```javascript
   async function callNewFeature() {
       const response = await fetch('/api/ad-analysis/new-feature', {
           credentials: 'same-origin'
       });
       const result = await response.json();
       // 결과 처리
   }
   ```

---

### 새 데이터베이스 테이블 추가

1. `database/schema.sql`에 DDL 추가
   ```sql
   CREATE TABLE ad_new_table (
       id INT PRIMARY KEY AUTO_INCREMENT,
       ...
   );
   ```

2. `app/utils/db_utils.py`에 쿼리 함수 추가 (필요시)

3. `app/services/`에 비즈니스 로직 추가

---

### 새 UI 탭 추가

1. `app/templates/ad_dashboard.html`에 탭 버튼 추가
   ```html
   <button class="tab" data-tab="new-tab">새 기능</button>
   ```

2. 탭 콘텐츠 추가
   ```html
   <div id="tab-new-tab" class="tab-content hidden">
       <!-- 콘텐츠 -->
   </div>
   ```

3. `app/static/js/ad_dashboard.js`에 이벤트 핸들러 추가

---

## 🎯 핵심 포인트

### ✅ 완성된 부분
- ✅ 완전한 Backend (17개 API)
- ✅ 완전한 Frontend (SPA)
- ✅ 완전한 Database 스키마
- ✅ 완전한 인증 시스템
- ✅ 완전한 분석 엔진
- ✅ 완전한 AI 통합
- ✅ 완전한 문서화

### ⏸️ 미완성 부분
- ⏸️ PDF/Excel 리포트 생성 로직 (엔드포인트만 존재)
- ⏸️ Excel 템플릿 파일 (가이드만 존재)
- ⏸️ 단위 테스트

### 🚀 즉시 가능
- 로컬 실행
- 프로덕션 배포
- 기능 테스트
- 사용자 테스트

---

**프로젝트 상태**: ✅ **95% 완료 - 즉시 사용 가능**

**작성자**: Claude Code
**날짜**: 2024-11-12
**버전**: 1.0.0
