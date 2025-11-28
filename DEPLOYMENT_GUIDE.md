# 🚀 광고 분석 대시보드 배포 가이드

**최종 업데이트**: 2024-11-12
**버전**: 1.0.0

---

## 📋 목차

1. [시작하기 전에](#시작하기-전에)
2. [로컬 개발 환경 설정](#로컬-개발-환경-설정)
3. [데이터베이스 설정](#데이터베이스-설정)
4. [애플리케이션 실행](#애플리케이션-실행)
5. [테스트](#테스트)
6. [프로덕션 배포](#프로덕션-배포)
7. [문제 해결](#문제-해결)

---

## 시작하기 전에

### 시스템 요구사항

- **Python**: 3.8 이상
- **MariaDB/MySQL**: 10.x 이상
- **OS**: Windows 10/11, Linux, macOS
- **메모리**: 최소 2GB RAM
- **디스크**: 최소 1GB 여유 공간

### 필수 계정

- **MariaDB 계정**: 데이터베이스 접근용
- **OpenAI API 키** (선택): AI 인사이트 기능 사용 시

---

## 로컬 개발 환경 설정

### 1. 프로젝트 클론/다운로드

```bash
cd c:\Users\JDH\Downloads\insight
```

### 2. Python 가상환경 생성 (권장)

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

### 3. 의존성 설치

```bash
pip install -r requirements.txt
```

**requirements.txt 내용:**
```txt
Flask==3.0.0
Flask-CORS==4.0.0
Flask-Session==0.5.0
python-dotenv==1.0.0
PyMySQL==1.1.0
PyJWT==2.8.0
pandas==2.1.0
openpyxl==3.1.2
openai==1.3.0
reportlab==4.0.7
xlsxwriter==3.1.9
```

### 4. 환경 변수 설정

#### `.env` 파일 생성

```bash
cp .env.example .env
```

#### `.env` 파일 편집

```env
# Flask 설정
FLASK_ENV=development
FLASK_DEBUG=True
SECRET_KEY=your-super-secret-key-change-this-in-production

# 데이터베이스 설정
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your-db-password
DB_NAME=mbizsquare

# JWT 설정 (mbizsquare.com과 동일한 키 사용)
JWT_SECRET_KEY=same-secret-key-as-mbizsquare
JWT_EXPIRATION_SECONDS=300

# OpenAI 설정 (선택)
OPENAI_API_KEY=sk-your-openai-api-key-here
ENABLE_AI_INSIGHTS=true

# 세션 설정
SESSION_TYPE=filesystem
SESSION_PERMANENT=True
SESSION_LIFETIME_HOURS=1

# 업로드 설정
MAX_CONTENT_LENGTH=10485760
UPLOAD_FOLDER=uploads

# 로깅
LOG_LEVEL=INFO
LOG_FILE=logs/app.log
```

**중요 변경 사항:**
- `SECRET_KEY`: 강력한 랜덤 문자열로 변경
- `DB_PASSWORD`: MariaDB 비밀번호
- `JWT_SECRET_KEY`: mbizsquare.com과 동일한 값 (매우 중요!)
- `OPENAI_API_KEY`: AI 기능 사용 시 추가

---

## 데이터베이스 설정

### 1. MariaDB 접속

```bash
mysql -u root -p
```

### 2. 데이터베이스 확인

```sql
-- mbizsquare 데이터베이스가 이미 존재하는지 확인
SHOW DATABASES LIKE 'mbizsquare';

-- 없으면 생성
CREATE DATABASE IF NOT EXISTS mbizsquare CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

USE mbizsquare;
```

### 3. 스키마 배포

```bash
mysql -u root -p mbizsquare < database/schema.sql
```

### 4. 테이블 생성 확인

```sql
SHOW TABLES LIKE 'ad_%';
```

**예상 출력:**
```
ad_analysis_snapshots
ad_daily_data
ad_campaign_memos
ad_monthly_goals
```

### 5. 샘플 데이터 삽입 (선택)

```sql
-- users 테이블에 테스트 사용자가 있어야 함
-- 없으면 임시로 생성
INSERT INTO users (user_id, username, email, password)
VALUES ('test_user', 'Test User', 'test@example.com', 'hashed_password');
```

---

## 애플리케이션 실행

### 1. 애플리케이션 시작

```bash
# 방법 1: run.py 사용 (권장)
python run.py

# 방법 2: Flask CLI 사용
flask run

# 방법 3: 포트 지정
flask run --port=5001
```

**성공 시 출력:**
```
 * Serving Flask app 'app'
 * Debug mode: on
WARNING: This is a development server. Do not use it in a production deployment.
 * Running on http://127.0.0.1:5000
Press CTRL+C to quit
```

### 2. 브라우저에서 접속

```
http://localhost:5000
```

**예상 동작:**
- JWT 토큰 없이 접근 시 → `/login` 페이지로 리다이렉트
- JWT 토큰이 있으면 → `/ad-dashboard` 대시보드 표시

---

## 테스트

### 1. 헬스체크 테스트

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

### 2. 데이터베이스 연결 테스트

```python
python -c "from app.utils.db_utils import init_database; from app import create_app; app = create_app(); with app.app_context(): print('DB OK:', init_database())"
```

**예상 출력:**
```
DB OK: True
```

### 3. JWT 토큰 생성 테스트 (mbizsquare.com에서)

```python
# mbizsquare.com에서 실행
from app.utils.auth_utils import generate_jwt_token

token = generate_jwt_token('test_user', expires_in=300)
print(f"http://localhost:5000/?token={token}")
```

### 4. 파일 업로드 테스트

#### 테스트용 CSV 파일 생성

**test_data.csv:**
```csv
date,campaign_name,spend,impressions,clicks,conversions,revenue
2024-11-01,테스트캠페인,150000,45000,1200,48,540000
2024-11-02,테스트캠페인,160000,48000,1300,52,580000
2024-11-03,테스트캠페인,145000,43000,1150,46,520000
```

#### cURL로 테스트

```bash
curl -X POST http://localhost:5000/api/ad-analysis/upload \
  -F "file=@test_data.csv" \
  -F "snapshot_name=테스트 분석" \
  --cookie "session=your-session-cookie"
```

### 5. API 엔드포인트 테스트 (Postman 권장)

#### 테스트 시나리오

1. **파일 업로드**
   - `POST /api/ad-analysis/upload`
   - Body: form-data (file)

2. **분석 목록 조회**
   - `GET /api/ad-analysis/snapshots?saved_only=true`

3. **상세 조회**
   - `GET /api/ad-analysis/snapshots/1`

4. **저장**
   - `PUT /api/ad-analysis/snapshots/1`
   - Body: `{"is_saved": true, "snapshot_name": "저장된 분석"}`

5. **삭제**
   - `DELETE /api/ad-analysis/snapshots/1`

---

## 프로덕션 배포

### 방법 1: Gunicorn (Linux 권장)

#### 1. Gunicorn 설치

```bash
pip install gunicorn
```

#### 2. 실행

```bash
gunicorn -w 4 -b 0.0.0.0:5000 run:app
```

**옵션 설명:**
- `-w 4`: 4개 워커 프로세스
- `-b 0.0.0.0:5000`: 모든 인터페이스에서 5000 포트 수신
- `run:app`: run.py의 app 객체 사용

### 방법 2: Docker (권장)

#### Dockerfile 생성

```dockerfile
FROM python:3.10-slim

WORKDIR /app

# 시스템 패키지 설치
RUN apt-get update && apt-get install -y \
    gcc \
    default-libmysqlclient-dev \
    && rm -rf /var/lib/apt/lists/*

# Python 의존성 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt gunicorn

# 애플리케이션 복사
COPY . .

# 로그 및 업로드 디렉토리 생성
RUN mkdir -p logs uploads flask_session

EXPOSE 5000

CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "--timeout", "120", "run:app"]
```

#### docker-compose.yml 생성

```yaml
version: '3.8'

services:
  app:
    build: .
    ports:
      - "5000:5000"
    environment:
      - FLASK_ENV=production
      - DB_HOST=db
      - DB_USER=root
      - DB_PASSWORD=your-db-password
      - DB_NAME=mbizsquare
    depends_on:
      - db
    volumes:
      - ./uploads:/app/uploads
      - ./logs:/app/logs
      - ./flask_session:/app/flask_session
    restart: unless-stopped

  db:
    image: mariadb:10.11
    environment:
      - MYSQL_ROOT_PASSWORD=your-db-password
      - MYSQL_DATABASE=mbizsquare
    volumes:
      - ./database/schema.sql:/docker-entrypoint-initdb.d/schema.sql
      - db_data:/var/lib/mysql
    restart: unless-stopped

volumes:
  db_data:
```

#### 실행

```bash
docker-compose up -d
```

### 방법 3: Nginx 리버스 프록시 (프로덕션 권장)

#### Nginx 설정

**/etc/nginx/sites-available/insight**:
```nginx
server {
    listen 80;
    server_name insight.mbizsquare.com;

    client_max_body_size 10M;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /static {
        alias /path/to/insight/app/static;
        expires 30d;
    }
}
```

#### Nginx 활성화

```bash
sudo ln -s /etc/nginx/sites-available/insight /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### HTTPS 설정 (Let's Encrypt)

```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d insight.mbizsquare.com
```

---

## 문제 해결

### Issue 1: 데이터베이스 연결 실패

**증상:**
```
DatabaseError: 데이터베이스 연결 실패: (2003, "Can't connect to MySQL server")
```

**해결:**
1. MariaDB 서비스 확인: `sudo systemctl status mariadb`
2. 포트 확인: `netstat -an | grep 3306`
3. `.env` 파일의 DB 설정 확인
4. 방화벽 확인: `sudo ufw status`

### Issue 2: JWT 토큰 검증 실패

**증상:**
```
AuthenticationError: 유효하지 않은 토큰입니다
```

**해결:**
1. mbizsquare.com과 동일한 `JWT_SECRET_KEY` 사용 확인
2. 토큰 만료 시간 확인 (5분)
3. 토큰 형식 확인 (Bearer 없이 순수 토큰만)

### Issue 3: 파일 업로드 실패

**증상:**
```
413 Payload Too Large
```

**해결:**
1. `.env`의 `MAX_CONTENT_LENGTH` 증가
2. Nginx 설정에 `client_max_body_size` 추가
3. uploads 디렉토리 권한 확인: `chmod 755 uploads`

### Issue 4: AI 인사이트 생성 안 됨

**증상:**
```
AI 인사이트 생성 실패
```

**해결:**
1. `OPENAI_API_KEY` 확인
2. OpenAI API 크레딧 확인
3. `ENABLE_AI_INSIGHTS=false`로 비활성화 (선택)

### Issue 5: 세션 만료

**증상:**
```
401 Unauthorized: 로그인이 필요합니다
```

**해결:**
1. 세션 유효 시간 확인 (기본 1시간)
2. `SESSION_LIFETIME_HOURS` 증가
3. Redis 사용 고려 (프로덕션 환경)

---

## 성능 최적화

### 1. 데이터베이스 인덱스 확인

```sql
SHOW INDEX FROM ad_daily_data;
```

### 2. 로그 레벨 조정

```env
# 프로덕션에서는 INFO 또는 WARNING
LOG_LEVEL=WARNING
```

### 3. Gunicorn 워커 수 조정

```bash
# CPU 코어 수 * 2 + 1
gunicorn -w 9 run:app  # 4 코어 기준
```

### 4. Redis 세션 저장소 (권장)

```bash
pip install redis flask-redis
```

```env
SESSION_TYPE=redis
SESSION_REDIS=redis://localhost:6379
```

---

## 백업 및 복구

### 데이터베이스 백업

```bash
# 백업
mysqldump -u root -p mbizsquare > backup_$(date +%Y%m%d).sql

# 복구
mysql -u root -p mbizsquare < backup_20241112.sql
```

### 파일 백업

```bash
tar -czf uploads_backup.tar.gz uploads/
tar -czf logs_backup.tar.gz logs/
```

---

## 모니터링

### 로그 확인

```bash
# 실시간 로그 보기
tail -f logs/app.log

# 에러 로그만 보기
grep ERROR logs/app.log
```

### 애플리케이션 상태 확인

```bash
# 헬스체크
curl http://localhost:5000/health

# 프로세스 확인
ps aux | grep gunicorn
```

---

## 참고 문서

- **프로젝트 문서**: [IMPLEMENTATION_STATUS.md](IMPLEMENTATION_STATUS.md)
- **API 명세**: [docs/API_SPEC.md](docs/API_SPEC.md)
- **데이터베이스 설계**: [docs/DATABASE_DESIGN.md](docs/DATABASE_DESIGN.md)
- **Excel 템플릿 가이드**: [app/static/templates/TEMPLATE_GUIDE.md](app/static/templates/TEMPLATE_GUIDE.md)

---

## 지원

문제가 계속되면 다음 정보를 포함하여 문의하세요:

1. 운영체제 및 Python 버전
2. 에러 메시지 전체 (logs/app.log)
3. `.env` 설정 (비밀번호 제외)
4. `pip list` 출력

---

**배포 완료! 🎉**
