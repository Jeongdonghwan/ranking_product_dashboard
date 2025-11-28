# 광고 분석 대시보드 아키텍처

## 시스템 개요

완전히 독립적인 Flask 웹 애플리케이션으로, JWT 토큰 기반 인증을 통해 메인 사이트(mbizsquare.com)와 연동됩니다.

## 아키텍처 다이어그램

```
┌─────────────────────────────────────────────────────────┐
│          https://mbizsquare.com (메인 사이트)            │
│  ┌───────────────────────────────────────────────────┐  │
│  │  헤더: [광고분석] 버튼                             │  │
│  │  클릭 시 → JWT 토큰 생성 (user_id 포함)           │  │
│  │  리다이렉트:                                       │  │
│  │  https://ad-insight.mbizsquare.com?token=xxx      │  │
│  └───────────────────────────────────────────────────┘  │
└───────────────────────┬─────────────────────────────────┘
                        │ JWT 토큰 전달
                        ↓
┌─────────────────────────────────────────────────────────┐
│    https://ad-insight.mbizsquare.com (Insight 앱)      │
│  ┌───────────────────────────────────────────────────┐  │
│  │  1. JWT 검증 (SECRET_KEY 사용)                    │  │
│  │  2. user_id 추출 및 DB 조회                       │  │
│  │  3. Flask 자체 세션 생성 (파일 기반)              │  │
│  │  4. 세션 쿠키 발급                                 │  │
│  │  5. 대시보드 표시                                  │  │
│  └───────────────────────────────────────────────────┘  │
│                                                           │
│  이후 접속: 세션 쿠키로 자동 인증 (JWT 불필요)          │
│                                                           │
│  ┌─────────────┐  ┌─────────────┐  ┌────────────────┐  │
│  │  Routes     │→ │  Services   │→ │  Models        │  │
│  │  (14 API)   │  │  (Analysis) │  │  (DB Queries)  │  │
│  └─────────────┘  └─────────────┘  └────────────────┘  │
└───────────────────────┬─────────────────────────────────┘
                        │
                        ↓
               ┌────────────────┐
               │    MariaDB     │
               │  (users 공유)  │
               │  + 4 신규 테이블│
               └────────────────┘
```

## 기술 스택

### Backend
- **Framework**: Flask 3.0.0
- **Language**: Python 3.10+
- **Database**: MariaDB (PyMySQL)
- **Authentication**: JWT (PyJWT)
- **Session**: Flask-Session (filesystem)
- **File Processing**: pandas, openpyxl
- **AI**: OpenAI GPT-4 (선택적)
- **Report**: reportlab, xlsxwriter
- **Server**: Gunicorn (운영 환경)

### Frontend
- **HTML5**: Semantic markup
- **CSS3**: Flexbox, Grid, Animations
- **JavaScript**: Vanilla JS (No framework)
- **Charting**: Chart.js 4.4.0
- **Icons**: Unicode/Emoji

### Infrastructure
- **Containerization**: Docker
- **Orchestration**: Docker Compose
- **Reverse Proxy**: Nginx (권장)

## 레이어 구조

### 1. Presentation Layer (프론트엔드)
```
templates/ad_dashboard.html
  ↓
static/js/ad_dashboard.js
  ↓
API 호출 (fetch)
```

**역할:**
- 사용자 인터페이스 렌더링
- 사용자 입력 처리
- Chart.js 차트 렌더링
- API 통신

### 2. API Layer (라우트)
```
routes/ad_analysis.py
  ↓
14개 RESTful 엔드포인트
  ↓
인증 검증 (@require_auth)
```

**역할:**
- HTTP 요청/응답 처리
- 입력 검증
- 세션 확인
- 에러 핸들링

### 3. Service Layer (비즈니스 로직)
```
services/ad_analyzer.py
  ↓
지표 계산, 비교 분석, 예산 페이싱
  ↓
services/ai_insights.py
  ↓
OpenAI GPT-4 인사이트 생성
```

**역할:**
- 복잡한 비즈니스 로직
- 데이터 분석 및 계산
- AI 통합

### 4. Data Layer (모델)
```
models/ad_models.py
  ↓
CRUD 함수들
  ↓
utils/db_utils.py
  ↓
MariaDB 연결 풀
```

**역할:**
- 데이터베이스 CRUD
- SQL 쿼리 실행
- 트랜잭션 관리

## 인증 플로우

### 첫 접속 (JWT 기반)
```
1. 사용자: 메인 사이트에서 [광고분석] 클릭

2. 메인 사이트:
   jwt_token = jwt.encode({
       'user_id': session['user_id'],
       'exp': datetime.utcnow() + timedelta(minutes=5)
   }, SECRET_KEY)

   redirect(f'https://ad-insight.mbizsquare.com?token={jwt_token}')

3. Insight 앱 (/ 라우트):
   token = request.args.get('token')
   payload = jwt.decode(token, SECRET_KEY)
   user_id = payload['user_id']

   # DB에서 사용자 조회
   user = get_user_by_id(user_id)

   # 세션 생성
   session['user_id'] = user_id
   session['user_name'] = user['user_nm']

   redirect('/ad-dashboard')

4. 사용자: 대시보드 표시
```

### 이후 접속 (세션 기반)
```
1. 사용자: https://ad-insight.mbizsquare.com 직접 접속

2. Insight 앱:
   if 'user_id' in session:
       # 세션 유효 → 대시보드 표시
       redirect('/ad-dashboard')
   else:
       # 세션 없음 → 메인 사이트 로그인으로 리다이렉트
       redirect('https://mbizsquare.com/login')
```

## 데이터 흐름

### 파일 업로드 플로우
```
사용자 → 파일 선택
  ↓
JavaScript: FormData 생성
  ↓
POST /api/ad-analysis/upload
  ↓
Route: 파일 검증 (확장자, 크기)
  ↓
pandas: read_excel() / read_csv()
  ↓
Route: 필수 컬럼 확인
  ↓
Service (AdAnalyzer):
  - save_snapshot() → DB 저장
  - calculate_metrics() → 지표 계산
  ↓
Service (AIInsights):
  - generate_insights() → OpenAI API 호출
  ↓
Route: 파일 삭제 (처리 완료)
  ↓
JSON 응답:
  {
    "success": true,
    "snapshot_id": 123,
    "metrics": {...},
    "insights": "..."
  }
  ↓
JavaScript:
  - 메트릭 카드 렌더링
  - Chart.js 차트 렌더링
  - AI 인사이트 표시
```

## 보안 고려사항

### 1. JWT 토큰
- **만료 시간**: 5분 (짧게 설정)
- **알고리즘**: HS256
- **Secret Key**: 메인 사이트와 동일한 키 사용
- **검증**: PyJWT로 서명 검증

### 2. 세션 관리
- **저장소**: Filesystem (운영에서는 Redis 권장)
- **쿠키 설정**:
  - `HttpOnly`: True (XSS 방지)
  - `Secure`: True (HTTPS only)
  - `SameSite`: 'Lax'
- **만료**: 1시간 (조정 가능)

### 3. SQL Injection 방지
- **Parameterized Query**: 모든 쿼리에 파라미터 바인딩 사용
- **ORM 미사용**: 직접 SQL이지만 안전한 방식

```python
# 안전한 예시
cursor.execute(
    "SELECT * FROM users WHERE user_id = %s",
    (user_id,)  # 파라미터 바인딩
)

# 위험한 예시 (사용 금지)
cursor.execute(
    f"SELECT * FROM users WHERE user_id = '{user_id}'"  # 직접 삽입
)
```

### 4. 파일 업로드 보안
- **확장자 검증**: .xlsx, .xls, .csv만 허용
- **크기 제한**: 10MB (설정 가능)
- **임시 저장**: uploads/ 디렉토리
- **처리 후 삭제**: 자동 정리

### 5. CORS 설정
```python
CORS(app, resources={
    r"/api/*": {
        "origins": ["https://mbizsquare.com"],
        "methods": ["GET", "POST", "PUT", "DELETE"],
        "allow_headers": ["Content-Type"]
    }
})
```

## 성능 최적화

### 1. 데이터베이스
- **인덱스**: user_id, date, snapshot_id에 복합 인덱스
- **JSON 컬럼**: 계산된 지표 캐싱 (metrics_summary)
- **연결 풀**: 재사용 가능한 연결 관리

### 2. 파일 처리
- **스트리밍**: 큰 파일 처리 시 메모리 절약
- **비동기 처리**: 추후 Celery 도입 가능

### 3. 프론트엔드
- **Chart.js**: 클라이언트 사이드 렌더링
- **Lazy Loading**: 필요할 때만 데이터 로드
- **캐싱**: 브라우저 캐시 활용

## 확장성

### 수평 확장 (Horizontal Scaling)
```
                  ┌─────────────┐
                  │  Nginx LB   │
                  └──────┬──────┘
                         │
         ┌───────────────┼───────────────┐
         │               │               │
    ┌────▼────┐    ┌────▼────┐    ┌────▼────┐
    │ App #1  │    │ App #2  │    │ App #3  │
    └────┬────┘    └────┬────┘    └────┬────┘
         │               │               │
         └───────────────┼───────────────┘
                         │
                  ┌──────▼──────┐
                  │   MariaDB   │
                  │  (Master)   │
                  └─────────────┘
```

**요구사항:**
- Redis 세션 스토어 (파일 세션 → Redis)
- 공유 파일 시스템 또는 S3

### 기능 확장
- **자동 데이터 수집**: 광고 플랫폼 API 연동
- **알림 기능**: 예산 초과 시 이메일/Slack
- **대시보드 커스터마이징**: 사용자별 레이아웃
- **다국어 지원**: i18n

## 모니터링

### 로깅
```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)
```

### 메트릭
- **응답 시간**: API 엔드포인트별
- **에러율**: 4xx, 5xx 응답
- **업로드 파일 크기**: 평균, 최대
- **AI API 비용**: OpenAI 토큰 사용량

### 헬스 체크
```python
@app.route('/health')
def health_check():
    return {
        'status': 'healthy',
        'database': check_db_connection(),
        'timestamp': datetime.now().isoformat()
    }
```

## 배포 전략

### Docker 컨테이너
```bash
# 빌드
docker build -t ad-insight:latest .

# 실행
docker run -d \
  -p 8001:5000 \
  --env-file .env \
  --name ad-insight-app \
  ad-insight:latest
```

### 무중단 배포
1. 새 버전 빌드
2. 새 컨테이너 시작
3. 헬스 체크 통과 확인
4. Nginx에서 트래픽 전환
5. 이전 컨테이너 종료

## 디렉토리 구조

```
insight/
├── app/                      # 애플리케이션 코드
│   ├── __init__.py          # Flask 앱 팩토리
│   ├── routes/              # API 엔드포인트
│   ├── services/            # 비즈니스 로직
│   ├── models/              # 데이터 모델
│   ├── utils/               # 유틸리티 함수
│   └── templates/           # HTML 템플릿
├── static/                   # 정적 파일
│   ├── css/
│   ├── js/
│   └── templates/           # Excel 템플릿
├── config/                   # 설정 파일
├── database/                 # 스키마 SQL
├── docs/                     # 문서
├── uploads/                  # 임시 파일
├── flask_session/           # 세션 파일
├── Dockerfile               # Docker 이미지
├── docker-compose.yml       # Docker Compose
├── requirements.txt         # Python 패키지
├── .env                     # 환경변수 (gitignore)
├── .env.example             # 환경변수 예제
└── run.py                   # 앱 실행
```

## 환경 분리

### Development (개발)
- DEBUG: True
- DB: localhost
- 세션: 파일 기반
- AI: 비활성화 (비용 절감)

### Production (운영)
- DEBUG: False
- DB: 실제 DB 서버
- 세션: Redis (권장)
- AI: 선택적 활성화
- HTTPS: 필수
- Gunicorn: 4 workers

## 참고 자료

- [Flask 공식 문서](https://flask.palletsprojects.com/)
- [Chart.js 문서](https://www.chartjs.org/docs/latest/)
- [JWT 표준](https://jwt.io/)
- [MariaDB 문서](https://mariadb.com/kb/en/)
