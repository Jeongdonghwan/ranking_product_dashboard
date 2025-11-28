# 📊 광고 분석 대시보드 (Ad Insight Dashboard)

완전히 독립적인 광고 분석 및 인사이트 도구

## ✨ 주요 기능

- **📤 데이터 입력**: Excel/CSV 드래그 & 드롭, 수기 입력
- **📊 실시간 분석**: ROAS, CTR, CPA, CVR 등 핵심 지표
- **📈 시각화**: Chart.js 기반 다축 차트, 일별 트렌드
- **💡 AI 인사이트**: OpenAI GPT-4 기반 마케팅 제안 (선택적)
- **🔄 기간 비교**: A/B 기간 비교 분석
- **🎯 목표 관리**: 월별 예산 및 목표 ROAS 설정
- **💾 분석 저장**: 태그, 메모와 함께 분석 저장
- **📄 리포트 생성**: PDF/Excel 다운로드

## 🚀 빠른 시작

### 1. 요구사항

- Python 3.10+
- MariaDB 10.3+
- (선택) Docker

### 2. 설치

```bash
# 저장소 클론
git clone <repository-url>
cd insight

# 가상환경 생성
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 의존성 설치
pip install -r requirements.txt
```

### 3. 환경 설정

```bash
# 환경변수 파일 복사
cp .env.example .env

# .env 파일 편집
# - SECRET_KEY: 강력한 랜덤 키 설정
# - JWT_SECRET_KEY: 메인 사이트와 동일한 키
# - DB_* : 데이터베이스 접속 정보
```

### 4. 데이터베이스 설정

```bash
# MariaDB 접속
mysql -u root -p

# 스키마 실행
USE mbizsquare;
SOURCE database/schema.sql;
```

### 5. 실행

```bash
python run.py
```

http://localhost:5000 접속

## 🐳 Docker로 실행

```bash
# 빌드 및 실행
docker-compose up -d

# 로그 확인
docker-compose logs -f

# 종료
docker-compose down
```

http://localhost:8001 접속

## 📁 프로젝트 구조

```
insight/
├── app/                      # 애플리케이션 코드
│   ├── __init__.py          # Flask 앱 팩토리
│   ├── routes/              # API 엔드포인트 (14개)
│   ├── services/            # 비즈니스 로직
│   ├── models/              # 데이터 모델
│   ├── utils/               # 유틸리티 함수
│   └── templates/           # HTML 템플릿
│
├── static/                   # 정적 파일
│   ├── css/                 # 스타일시트
│   ├── js/                  # JavaScript
│   └── templates/           # Excel 템플릿
│
├── config/                   # 설정 파일
├── database/                 # DB 스키마
├── docs/                     # 문서
│   ├── ARCHITECTURE.md      # 아키텍처
│   ├── API_SPEC.md          # API 명세
│   ├── DATABASE_DESIGN.md   # DB 설계
│   ├── DESIGN_SYSTEM.md     # 디자인 가이드
│   ├── ISSUES.md            # 알려진 이슈
│   └── DEPLOYMENT.md        # 배포 가이드
│
├── uploads/                  # 임시 파일
├── logs/                     # 로그 파일
├── flask_session/           # 세션 파일
│
├── Dockerfile               # Docker 이미지
├── docker-compose.yml       # Docker Compose
├── requirements.txt         # Python 패키지
├── .env.example             # 환경변수 예제
├── .gitignore              # Git 제외 파일
├── run.py                   # 앱 실행 스크립트
└── README.md                # 이 파일
```

## 🔑 핵심 개념

### 인증 플로우

1. 사용자가 메인 사이트(mbizsquare.com)에서 [광고분석] 클릭
2. 메인 사이트에서 JWT 토큰 생성 (user_id 포함, 5분 유효)
3. Insight 앱으로 리다이렉트 (토큰을 URL 파라미터로 전달)
4. Insight 앱에서 JWT 검증 → 자체 세션 생성
5. 이후 접속은 세션 쿠키로 자동 인증

### 데이터 처리

```
파일 업로드 → pandas 파싱 → DB 저장 → 지표 계산 → AI 인사이트
```

- **원본 데이터**: data_json (TEXT)
- **계산된 지표**: metrics_summary (JSON) - 캐싱
- **일별 데이터**: ad_daily_data 테이블

## 📊 API 엔드포인트

### 인증
- `GET /` - JWT 검증 및 세션 생성
- `GET /ad-dashboard` - 대시보드 페이지

### 데이터 입력
- `POST /api/ad-analysis/upload` - 파일 업로드
- `POST /api/ad-analysis/manual-input` - 수기 입력

### 분석 관리
- `GET /api/ad-analysis/snapshots` - 목록 조회
- `GET /api/ad-analysis/snapshots/:id` - 상세 조회
- `PUT /api/ad-analysis/snapshots/:id` - 수정
- `DELETE /api/ad-analysis/snapshots/:id` - 삭제

### 분석 기능
- `GET /api/ad-analysis/compare` - 기간 비교
- `GET /api/ad-analysis/budget-pacing` - 예산 페이싱
- `GET/POST /api/ad-analysis/goals` - 목표 관리
- `GET/POST /api/ad-analysis/memos` - 메모 관리

### 리포트
- `GET /api/ad-analysis/export/pdf/:id` - PDF 다운로드
- `GET /api/ad-analysis/export/excel/:id` - Excel 다운로드
- `GET /api/ad-analysis/template/:type` - 템플릿 다운로드

## 🎨 기술 스택

### Backend
- Flask 3.0
- PyMySQL
- pandas, openpyxl
- OpenAI GPT-4
- PyJWT

### Frontend
- Vanilla JavaScript (No framework)
- Chart.js
- HTML5/CSS3

### Infrastructure
- Docker
- Gunicorn
- Nginx (리버스 프록시)

## 📖 문서

- [아키텍처](docs/ARCHITECTURE.md) - 시스템 설계 및 구조
- [API 명세서](docs/API_SPEC.md) - 전체 API 엔드포인트
- [DB 설계](docs/DATABASE_DESIGN.md) - 테이블 스키마 및 ERD
- [디자인 시스템](docs/DESIGN_SYSTEM.md) - UI/UX 가이드
- [알려진 이슈](docs/ISSUES.md) - 문제 해결 방법
- [배포 가이드](docs/DEPLOYMENT.md) - 상세 배포 방법

## 🔧 개발

### 개발 서버 실행

```bash
python run.py
```

### 테스트

```bash
pytest tests/
```

### 로그 확인

```bash
tail -f logs/app.log
```

## 🚢 배포

### 운영 환경 설정

```bash
# .env 파일 수정
FLASK_ENV=production
SECRET_KEY=강력한-랜덤-키
AI_INSIGHTS_ENABLED=true
```

### Docker 배포

```bash
docker-compose -f docker-compose.yml up -d
```

자세한 내용은 [배포 가이드](docs/DEPLOYMENT.md) 참조

## 🔐 보안

- JWT 토큰 만료: 5분
- 세션 쿠키: HttpOnly, Secure (HTTPS)
- SQL Injection 방지: Parameterized Queries
- 파일 업로드 검증: 확장자 + MIME 타입
- CORS 설정: 메인 사이트만 허용

## 📝 라이선스

MIT License

## 👥 기여

Issues 및 Pull Requests 환영합니다!

## 📞 문의

- GitHub Issues
- Email: support@mbizsquare.com

---

**Made with ❤️ for mbizsquare.com**
