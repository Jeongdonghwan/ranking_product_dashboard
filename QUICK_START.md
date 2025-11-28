# 🚀 빠른 시작 가이드

**광고 분석 대시보드 - 5분 안에 시작하기**

---

## ✅ 사전 준비

- Python 3.8+
- MariaDB 10.x+
- 텍스트 에디터

---

## 📦 1단계: 의존성 설치 (1분)

```bash
cd c:\Users\JDH\Downloads\insight

# 가상환경 생성 (선택)
python -m venv venv
venv\Scripts\activate

# 패키지 설치
pip install -r requirements.txt
```

---

## 🗄️ 2단계: 데이터베이스 설정 (2분)

```bash
# MariaDB 접속
mysql -u root -p

# 데이터베이스 선택
USE mbizsquare;

# 스키마 배포
SOURCE database/schema.sql;

# 확인
SHOW TABLES LIKE 'ad_%';
```

**결과:** 4개 테이블이 생성됨
```
ad_analysis_snapshots
ad_daily_data
ad_campaign_memos
ad_monthly_goals
```

---

## ⚙️ 3단계: 환경 변수 설정 (1분)

`.env` 파일 생성:

```env
# Flask 설정
FLASK_ENV=development
FLASK_DEBUG=True
SECRET_KEY=your-super-secret-key-change-this

# 데이터베이스 (실제 값으로 변경!)
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your-db-password
DB_NAME=mbizsquare

# JWT (mbizsquare.com과 동일한 키!)
JWT_SECRET_KEY=same-secret-key-as-mbizsquare
JWT_EXPIRATION_SECONDS=300

# OpenAI (선택)
OPENAI_API_KEY=sk-your-api-key-here
ENABLE_AI_INSIGHTS=true

# 세션
SESSION_TYPE=filesystem
SESSION_PERMANENT=True
SESSION_LIFETIME_HOURS=1
```

**중요:**
- `DB_PASSWORD`: MariaDB 비밀번호로 변경
- `JWT_SECRET_KEY`: mbizsquare.com과 동일한 값 사용 (필수!)
- `SECRET_KEY`: 랜덤 문자열 생성

---

## 🎯 4단계: 실행 (30초)

```bash
python run.py
```

**성공 시 출력:**
```
 * Serving Flask app 'app'
 * Debug mode: on
 * Running on http://127.0.0.1:5000
```

브라우저에서 접속:
```
http://localhost:5000
```

---

## 🧪 5단계: 테스트 (30초)

### A. 헬스체크

```bash
curl http://localhost:5000/health
```

**예상 응답:**
```json
{
  "status": "ok",
  "service": "insight"
}
```

### B. 데이터베이스 연결 확인

```python
python -c "from app.utils.db_utils import get_db_connection; conn = get_db_connection(); print('DB OK:', conn is not None); conn.close()"
```

**예상 출력:**
```
DB OK: True
```

---

## 📊 6단계: 테스트 데이터 업로드

### 테스트 CSV 생성

`test_data.csv` 파일 생성:

```csv
date,campaign_name,spend,impressions,clicks,conversions,revenue
2024-11-01,테스트캠페인,150000,45000,1200,48,540000
2024-11-02,테스트캠페인,160000,48000,1300,52,580000
2024-11-03,테스트캠페인,145000,43000,1150,46,520000
```

### 대시보드에서 업로드

1. http://localhost:5000 접속
2. "데이터 입력" 탭
3. `test_data.csv` 드래그 앤 드롭
4. "분석 결과" 탭에서 확인

---

## 🎉 완료!

이제 다음 기능을 사용할 수 있습니다:

✅ **데이터 입력**
- Excel/CSV 파일 업로드
- 수기 데이터 입력

✅ **실시간 분석**
- ROAS, CTR, CPA, CVR 지표
- 일별 트렌드 차트
- 캠페인별 성과 순위

✅ **AI 인사이트** (OpenAI 키 설정 시)
- 자동 인사이트 생성
- 실행 가능한 액션 제안

✅ **분석 저장 및 비교**
- 분석 저장 및 태그 관리
- 기간 비교 분석

✅ **목표 관리**
- 월별 예산 및 목표 ROAS 설정
- 예산 소진율 모니터링

---

## 🔧 문제 해결

### 문제 1: 데이터베이스 연결 실패

```bash
# MariaDB 서비스 확인
# Windows
services.msc에서 MySQL 서비스 확인

# Linux
sudo systemctl status mariadb
```

### 문제 2: JWT 토큰 검증 실패

- `.env`의 `JWT_SECRET_KEY`가 mbizsquare.com과 동일한지 확인
- 토큰 만료 시간 확인 (기본 5분)

### 문제 3: 파일 업로드 실패

```bash
# uploads 디렉토리 권한 확인
mkdir uploads
chmod 755 uploads  # Linux/Mac
```

### 문제 4: 모듈 import 오류

```bash
# 패키지 재설치
pip install --upgrade -r requirements.txt
```

---

## 📚 다음 단계

- **배포**: [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) 참조
- **API 명세**: [docs/API_SPEC.md](docs/API_SPEC.md) 참조
- **템플릿 가이드**: [app/static/templates/TEMPLATE_GUIDE.md](app/static/templates/TEMPLATE_GUIDE.md) 참조

---

## 🆘 지원

문제가 계속되면:

1. `logs/app.log` 확인
2. Python 버전 확인: `python --version`
3. 패키지 목록 확인: `pip list`

---

**제작**: mbizsquare.com
**버전**: 1.0.0
**최종 업데이트**: 2024-11-12
