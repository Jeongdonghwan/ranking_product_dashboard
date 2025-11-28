# 배포 가이드

## 목차
1. [로컬 개발 환경 구축](#로컬-개발-환경-구축)
2. [Docker 배포](#docker-배포)
3. [운영 환경 배포](#운영-환경-배포)
4. [데이터베이스 설정](#데이터베이스-설정)
5. [환경변수 설정](#환경변수-설정)
6. [메인 사이트 통합](#메인-사이트-통합)
7. [모니터링 및 유지보수](#모니터링-및-유지보수)

---

## 로컬 개발 환경 구축

### 1. 사전 요구사항

- **Python**: 3.10 이상
- **MariaDB**: 10.3 이상
- **Git**: 최신 버전
- **OS**: Windows 10/11, macOS, Linux

### 2. 저장소 클론

```bash
cd c:\Users\JDH\Downloads
# 이미 insight 디렉토리가 있음
cd insight
```

### 3. 가상환경 생성 및 활성화

**Windows**:
```bash
python -m venv venv
venv\Scripts\activate
```

**macOS/Linux**:
```bash
python3 -m venv venv
source venv/bin/activate
```

### 4. 의존성 설치

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

**예상 소요 시간**: 2-3분

### 5. 환경변수 설정

```bash
# .env.example을 .env로 복사
copy .env.example .env  # Windows
# cp .env.example .env  # macOS/Linux

# .env 파일 편집 (VS Code, 메모장 등)
notepad .env
```

**.env 파일 예시**:
```bash
# Flask 설정
FLASK_ENV=development
SECRET_KEY=dev-secret-key-change-in-production
JWT_SECRET_KEY=same-as-main-site-secret-key

# 데이터베이스
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_password
DB_NAME=mbizsquare

# OpenAI (선택적)
OPENAI_API_KEY=
AI_INSIGHTS_ENABLED=false

# 파일 업로드
MAX_FILE_SIZE_MB=10

# 메인 사이트 URL
MAIN_SITE_URL=http://localhost:3000
```

### 6. 데이터베이스 테이블 생성

```bash
# MariaDB 접속
mysql -u root -p

# 데이터베이스 선택
USE mbizsquare;

# 스키마 실행
SOURCE database/schema.sql;

# 테이블 확인
SHOW TABLES LIKE 'ad_%';
```

**결과**:
```
+-------------------------+
| Tables_in_mbizsquare    |
+-------------------------+
| ad_analysis_snapshots   |
| ad_campaign_memos       |
| ad_daily_data           |
| ad_monthly_goals        |
+-------------------------+
```

### 7. 앱 실행

```bash
python run.py
```

**출력**:
```
 * Serving Flask app 'app'
 * Debug mode: on
 * Running on http://127.0.0.1:5000
```

### 8. 브라우저 접속

```
http://localhost:5000
```

**주의**: 로컬 개발 환경에서는 JWT 토큰 없이 테스트 가능하도록 설정 필요:

```python
# app/__init__.py (개발 모드만)
if app.config['ENV'] == 'development':
    @app.before_request
    def bypass_auth():
        if 'user_id' not in session:
            session['user_id'] = 'test_user'  # 테스트 사용자
```

---

## Docker 배포

### 1. Docker 설치 확인

```bash
docker --version
docker-compose --version
```

### 2. Docker 이미지 빌드

```bash
# insight 디렉토리에서
docker build -t ad-insight:latest .
```

**예상 소요 시간**: 5-10분 (최초)

### 3. Docker Compose로 실행

```bash
docker-compose up -d
```

**서비스 확인**:
```bash
docker-compose ps
```

**결과**:
```
NAME                COMMAND                  SERVICE      STATUS     PORTS
ad-insight-app      "gunicorn --bind 0.0…"   ad-insight   Up         0.0.0.0:8001->5000/tcp
```

### 4. 로그 확인

```bash
# 전체 로그
docker-compose logs -f

# 특정 서비스 로그
docker-compose logs -f ad-insight
```

### 5. 컨테이너 내부 접속

```bash
docker-compose exec ad-insight bash
```

### 6. 종료 및 재시작

```bash
# 중지
docker-compose stop

# 재시작
docker-compose restart

# 완전 삭제 (데이터 포함)
docker-compose down -v
```

---

## 운영 환경 배포

### 1. 서버 준비

**최소 사양**:
- CPU: 2 Core
- RAM: 4GB
- 디스크: 20GB SSD
- OS: Ubuntu 20.04 LTS 이상

### 2. 서버 소프트웨어 설치

```bash
# 시스템 업데이트
sudo apt update && sudo apt upgrade -y

# Docker 설치
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Docker Compose 설치
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Git 설치
sudo apt install git -y
```

### 3. 애플리케이션 배포

```bash
# 애플리케이션 디렉토리 생성
sudo mkdir -p /var/www/ad-insight
cd /var/www/ad-insight

# 코드 업로드 (Git 또는 SCP)
git clone <repository-url> .
# 또는
scp -r local/insight/* user@server:/var/www/ad-insight/

# 환경변수 설정
sudo cp .env.example .env
sudo nano .env  # 운영 환경 설정 입력
```

**운영 환경 .env**:
```bash
FLASK_ENV=production
SECRET_KEY=강력한-랜덤-키-사용
JWT_SECRET_KEY=메인-사이트와-동일한-키

DB_HOST=db.mbizsquare.com
DB_PORT=3306
DB_USER=ad_insight_user
DB_PASSWORD=강력한-비밀번호
DB_NAME=mbizsquare

OPENAI_API_KEY=sk-실제-API-키
AI_INSIGHTS_ENABLED=true

MAIN_SITE_URL=https://mbizsquare.com
```

### 4. Docker Compose 실행

```bash
sudo docker-compose -f docker-compose.yml up -d
```

### 5. Nginx 리버스 프록시 설정

```bash
# Nginx 설치
sudo apt install nginx -y

# 설정 파일 생성
sudo nano /etc/nginx/sites-available/ad-insight
```

**Nginx 설정**:
```nginx
server {
    listen 80;
    server_name ad-insight.mbizsquare.com;

    # HTTP to HTTPS 리다이렉트
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name ad-insight.mbizsquare.com;

    # SSL 인증서 (Let's Encrypt)
    ssl_certificate /etc/letsencrypt/live/ad-insight.mbizsquare.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/ad-insight.mbizsquare.com/privkey.pem;

    # SSL 설정
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    # 로그
    access_log /var/log/nginx/ad-insight-access.log;
    error_log /var/log/nginx/ad-insight-error.log;

    # 프록시 설정
    location / {
        proxy_pass http://localhost:8001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # 타임아웃 (파일 업로드용)
        proxy_connect_timeout 120s;
        proxy_send_timeout 120s;
        proxy_read_timeout 120s;

        # 파일 업로드 크기 제한
        client_max_body_size 10M;
    }

    # 정적 파일 직접 서빙 (선택적)
    location /static/ {
        alias /var/www/ad-insight/static/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
```

```bash
# 설정 활성화
sudo ln -s /etc/nginx/sites-available/ad-insight /etc/nginx/sites-enabled/

# Nginx 설정 테스트
sudo nginx -t

# Nginx 재시작
sudo systemctl restart nginx
```

### 6. SSL 인증서 발급 (Let's Encrypt)

```bash
# Certbot 설치
sudo apt install certbot python3-certbot-nginx -y

# 인증서 발급
sudo certbot --nginx -d ad-insight.mbizsquare.com

# 자동 갱신 확인
sudo certbot renew --dry-run
```

### 7. 방화벽 설정

```bash
# UFW 활성화
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw allow 22/tcp  # SSH
sudo ufw enable
```

---

## 데이터베이스 설정

### 1. 전용 데이터베이스 사용자 생성 (권장)

```sql
-- MariaDB에 접속
mysql -u root -p

-- 사용자 생성
CREATE USER 'ad_insight_user'@'%' IDENTIFIED BY '강력한_비밀번호';

-- 권한 부여
GRANT SELECT, INSERT, UPDATE, DELETE ON mbizsquare.ad_analysis_snapshots TO 'ad_insight_user'@'%';
GRANT SELECT, INSERT, UPDATE, DELETE ON mbizsquare.ad_daily_data TO 'ad_insight_user'@'%';
GRANT SELECT, INSERT, UPDATE, DELETE ON mbizsquare.ad_campaign_memos TO 'ad_insight_user'@'%';
GRANT SELECT, INSERT, UPDATE, DELETE ON mbizsquare.ad_monthly_goals TO 'ad_insight_user'@'%';
GRANT SELECT ON mbizsquare.users TO 'ad_insight_user'@'%';

-- 권한 적용
FLUSH PRIVILEGES;
```

### 2. 백업 설정

```bash
# 백업 스크립트 생성
sudo nano /usr/local/bin/backup-ad-insight-db.sh
```

**backup-ad-insight-db.sh**:
```bash
#!/bin/bash

# 설정
DB_USER="ad_insight_user"
DB_PASS="비밀번호"
DB_NAME="mbizsquare"
BACKUP_DIR="/var/backups/ad-insight"
DATE=$(date +%Y%m%d_%H%M%S)

# 백업 디렉토리 생성
mkdir -p $BACKUP_DIR

# 백업 실행
mysqldump -u $DB_USER -p$DB_PASS $DB_NAME \
  ad_analysis_snapshots \
  ad_daily_data \
  ad_campaign_memos \
  ad_monthly_goals \
  > $BACKUP_DIR/backup_$DATE.sql

# 7일 이상 된 백업 삭제
find $BACKUP_DIR -type f -mtime +7 -delete

echo "백업 완료: $BACKUP_DIR/backup_$DATE.sql"
```

```bash
# 실행 권한 부여
sudo chmod +x /usr/local/bin/backup-ad-insight-db.sh

# 크론 작업 등록 (매일 새벽 3시)
sudo crontab -e

# 다음 라인 추가
0 3 * * * /usr/local/bin/backup-ad-insight-db.sh >> /var/log/backup-ad-insight.log 2>&1
```

---

## 환경변수 설정

### 개발 환경
```bash
FLASK_ENV=development
SECRET_KEY=dev-secret-key
JWT_SECRET_KEY=dev-jwt-key
DB_HOST=localhost
AI_INSIGHTS_ENABLED=false
```

### 운영 환경
```bash
FLASK_ENV=production
SECRET_KEY=$(openssl rand -base64 32)  # 강력한 랜덤 키
JWT_SECRET_KEY=메인-사이트와-동일
DB_HOST=db.mbizsquare.com
AI_INSIGHTS_ENABLED=true
```

### SECRET_KEY 생성 방법

```bash
# Python으로 생성
python -c "import secrets; print(secrets.token_urlsafe(32))"

# OpenSSL로 생성
openssl rand -base64 32
```

---

## 메인 사이트 통합

### 1. 메인 사이트에 JWT 생성 코드 추가

**routes/ad_insight.py** (메인 사이트):
```python
from flask import Blueprint, session, redirect
import jwt
from datetime import datetime, timedelta

ad_insight_bp = Blueprint('ad_insight', __name__)

@ad_insight_bp.route('/ad-insight-link')
def get_ad_insight_link():
    """광고 분석 대시보드로 이동"""
    # 로그인 확인
    if 'user_id' not in session:
        return redirect('/login?next=/ad-insight-link')

    # JWT 토큰 생성 (5분 유효)
    token = jwt.encode({
        'user_id': session['user_id'],
        'exp': datetime.utcnow() + timedelta(minutes=5)
    }, current_app.config['SECRET_KEY'], algorithm='HS256')

    # Insight 앱으로 리다이렉트
    insight_url = current_app.config.get('AD_INSIGHT_URL', 'https://ad-insight.mbizsquare.com')
    return redirect(f'{insight_url}?token={token}')
```

**app.py** (메인 사이트):
```python
from routes.ad_insight import ad_insight_bp

app.register_blueprint(ad_insight_bp)
```

### 2. 메인 사이트 헤더에 링크 추가

**templates/header.html**:
```html
<nav>
  <a href="/">홈</a>
  <a href="/ad-insight-link">광고 분석</a>
  <a href="/profile">프로필</a>
  <a href="/logout">로그아웃</a>
</nav>
```

### 3. 환경변수 추가 (메인 사이트)

```bash
# 메인 사이트 .env
AD_INSIGHT_URL=https://ad-insight.mbizsquare.com
```

---

## 모니터링 및 유지보수

### 1. 로그 설정

**app/__init__.py**:
```python
import logging
from logging.handlers import RotatingFileHandler

if not app.debug:
    file_handler = RotatingFileHandler(
        'logs/app.log',
        maxBytes=10*1024*1024,  # 10MB
        backupCount=10
    )
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    ))
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.setLevel(logging.INFO)
    app.logger.info('Ad Insight 시작')
```

### 2. 헬스 체크 엔드포인트

**app/routes/health.py**:
```python
from flask import Blueprint, jsonify
from app.utils.db_utils import get_db_connection

health_bp = Blueprint('health', __name__)

@health_bp.route('/health')
def health_check():
    """헬스 체크 엔드포인트"""
    try:
        # DB 연결 확인
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        cursor.close()
        conn.close()
        db_status = "healthy"
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"

    return jsonify({
        'status': 'healthy' if db_status == 'healthy' else 'unhealthy',
        'database': db_status,
        'timestamp': datetime.now().isoformat()
    })
```

### 3. Uptime 모니터링

**UptimeRobot, Pingdom 등 사용**:
```
URL: https://ad-insight.mbizsquare.com/health
간격: 5분
알림: 이메일, Slack
```

### 4. 로그 분석

```bash
# 에러 로그 확인
sudo grep ERROR /var/log/nginx/ad-insight-error.log

# 접속 통계
sudo tail -f /var/log/nginx/ad-insight-access.log

# Docker 로그
docker-compose logs --tail=100 -f
```

### 5. 성능 모니터링

```bash
# CPU/메모리 사용량
docker stats ad-insight-app

# 디스크 사용량
df -h

# 데이터베이스 크기
mysql -u root -p -e "
SELECT
  table_name,
  ROUND(((data_length + index_length) / 1024 / 1024), 2) AS 'Size (MB)'
FROM information_schema.TABLES
WHERE table_schema = 'mbizsquare'
  AND table_name LIKE 'ad_%';"
```

---

## 업데이트 및 재배포

### 1. 무중단 배포 (Blue-Green)

```bash
# 1. 새 버전 빌드
docker build -t ad-insight:v2 .

# 2. 새 컨테이너 시작 (다른 포트)
docker run -d -p 8002:5000 --name ad-insight-v2 ad-insight:v2

# 3. 헬스 체크
curl http://localhost:8002/health

# 4. Nginx 설정 변경 (8001 → 8002)
sudo nano /etc/nginx/sites-available/ad-insight

# 5. Nginx 재시작
sudo systemctl reload nginx

# 6. 이전 컨테이너 종료
docker stop ad-insight-app
docker rm ad-insight-app
```

### 2. 롤링 업데이트 (Docker Compose)

```bash
# docker-compose.yml 업데이트
docker-compose pull
docker-compose up -d --no-deps --build ad-insight
```

---

## 문제 해결 (Troubleshooting)

### 문제 1: 컨테이너가 시작되지 않음

```bash
# 로그 확인
docker-compose logs ad-insight

# 일반적인 원인:
# - 환경변수 누락
# - DB 연결 실패
# - 포트 충돌
```

### 문제 2: 데이터베이스 연결 실패

```bash
# DB 접속 테스트
mysql -h DB_HOST -P DB_PORT -u DB_USER -p

# 방화벽 확인
sudo ufw status

# MariaDB 원격 접속 허용
sudo nano /etc/mysql/mariadb.conf.d/50-server.cnf
# bind-address = 0.0.0.0
```

### 문제 3: 파일 업로드 실패

```bash
# 업로드 디렉토리 권한 확인
ls -la uploads/

# 권한 부여
chmod 777 uploads/

# Nginx 파일 크기 제한 확인
sudo nano /etc/nginx/nginx.conf
# client_max_body_size 10M;
```

---

## 체크리스트

### 배포 전
- [ ] 환경변수 설정 완료
- [ ] 데이터베이스 테이블 생성
- [ ] SECRET_KEY 생성 및 설정
- [ ] SSL 인증서 발급
- [ ] 방화벽 설정
- [ ] 백업 스크립트 설정

### 배포 후
- [ ] 헬스 체크 엔드포인트 확인
- [ ] 파일 업로드 테스트
- [ ] AI 인사이트 생성 테스트
- [ ] 메인 사이트 연동 확인
- [ ] 로그 모니터링 설정
- [ ] 백업 자동화 확인

---

## 참고 자료

- [Flask 배포 가이드](https://flask.palletsprojects.com/en/2.3.x/deploying/)
- [Docker 공식 문서](https://docs.docker.com/)
- [Nginx 설정 가이드](https://nginx.org/en/docs/)
- [Let's Encrypt](https://letsencrypt.org/)
