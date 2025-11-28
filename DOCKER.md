# Docker 배포 가이드

광고 분석 대시보드를 Docker Compose를 사용하여 프로덕션 환경에 배포하는 방법입니다.

## 🎯 시스템 요구사항

- **Docker**: 20.10 이상
- **Docker Compose**: 2.0 이상
- **메모리**: 최소 4GB (권장 8GB)
- **CPU**: 최소 2코어 (권장 4코어)
- **디스크**: 최소 20GB

---

## 📦 배포 구성

Docker Compose는 다음 서비스를 자동으로 실행합니다:

1. **app**: Flask 애플리케이션 (Gunicorn + Python 3.10)
2. **db**: MariaDB 10.11 (데이터베이스)
3. **redis**: Redis 7 (세션 저장소)
4. **nginx**: Nginx (선택사항, 리버스 프록시)

---

## 🚀 빠른 시작

### 1. 환경 변수 설정

```bash
# .env 파일 생성
cp .env.example .env

# .env 파일 수정 (필수!)
nano .env  # 또는 vi, code 등
```

**필수 설정 항목:**
```env
# Flask Secret Key (32자 이상 랜덤 문자열)
SECRET_KEY=your-production-secret-key-min-32-characters

# JWT Secret (mbizsquare.com과 동일한 값)
JWT_SECRET_KEY=same-as-mbizsquare-com-jwt-secret

# MariaDB 비밀번호
DB_ROOT_PASSWORD=your-secure-root-password
DB_PASSWORD=your-secure-db-password

# OpenAI API Key
OPENAI_API_KEY=sk-your-openai-api-key-here
```

**Secret Key 생성 방법:**
```bash
python -c "import os; print(os.urandom(32).hex())"
```

### 2. Docker 이미지 빌드 및 실행

```bash
# 백그라운드로 실행
docker-compose up -d --build

# 또는 로그 보며 실행
docker-compose up --build
```

### 3. 서비스 확인

```bash
# 컨테이너 상태 확인
docker-compose ps

# 로그 확인
docker-compose logs -f app

# 헬스체크
curl http://localhost:8080/health
```

---

## 🔧 상세 설정

### Gunicorn 워커 설정

`.env` 파일에서 워커 수와 타임아웃을 조정할 수 있습니다:

```env
# 워커 프로세스 수 (기본: CPU 코어 * 2 + 1)
GUNICORN_WORKERS=4

# 요청 타임아웃 (초)
GUNICORN_TIMEOUT=120

# 워커 클래스 (sync, gevent)
GUNICORN_WORKER_CLASS=sync
```

**권장 워커 수 계산:**
- **CPU 2코어**: workers=4 (기본값)
- **CPU 4코어**: workers=8
- **CPU 8코어**: workers=16

### 리소스 제한 조정

`docker-compose.yml`에서 리소스 제한을 수정할 수 있습니다:

```yaml
services:
  app:
    deploy:
      resources:
        limits:
          cpus: '2.0'      # 최대 CPU 사용량
          memory: 2G        # 최대 메모리 사용량
        reservations:
          cpus: '0.5'      # 보장 CPU
          memory: 512M      # 보장 메모리
```

### Redis 세션 활성화

Docker 환경에서는 기본적으로 Redis 세션이 활성화됩니다:

```env
SESSION_TYPE=redis
REDIS_URL=redis://redis:6379/0
```

---

## 📊 모니터링

### 실시간 리소스 사용량

```bash
# CPU/메모리 사용량 확인
docker stats

# 특정 컨테이너만 확인
docker stats insight_app
```

### 로그 확인

```bash
# 전체 로그
docker-compose logs

# 특정 서비스 로그
docker-compose logs app
docker-compose logs db
docker-compose logs redis

# 실시간 로그 스트리밍
docker-compose logs -f app

# 최근 100줄
docker-compose logs --tail=100 app
```

### 컨테이너 내부 접속

```bash
# Flask 애플리케이션 컨테이너
docker exec -it insight_app bash

# MariaDB 컨테이너
docker exec -it insight_db bash

# Redis 컨테이너
docker exec -it insight_redis sh
```

---

## 🔄 운영 명령어

### 서비스 재시작

```bash
# 전체 재시작
docker-compose restart

# 특정 서비스만 재시작
docker-compose restart app
```

### 서비스 중지/시작

```bash
# 중지 (컨테이너 유지)
docker-compose stop

# 시작
docker-compose start

# 완전 종료 (컨테이너 삭제)
docker-compose down

# 볼륨까지 삭제 (데이터베이스 초기화)
docker-compose down -v
```

### 스케일링

```bash
# Flask 앱 3개로 증가 (로드 밸런싱)
docker-compose up -d --scale app=3
```

### 이미지 업데이트

```bash
# 코드 변경 후 재빌드
docker-compose build --no-cache app

# 재시작
docker-compose up -d app
```

---

## 🛠 트러블슈팅

### 1. 컨테이너가 시작되지 않음

```bash
# 로그 확인
docker-compose logs app

# 컨테이너 상태 확인
docker-compose ps

# 헬스체크 확인
docker inspect insight_app | grep -A 10 Health
```

**일반적인 원인:**
- `.env` 파일 누락 또는 잘못된 설정
- 포트 충돌 (8080 포트가 이미 사용 중)
- 메모리 부족

### 2. 데이터베이스 연결 실패

```bash
# MariaDB 컨테이너 로그 확인
docker-compose logs db

# 연결 테스트
docker exec -it insight_db mysql -u root -p
```

**해결 방법:**
- `DB_ROOT_PASSWORD` 확인
- 데이터베이스 초기화: `docker-compose down -v && docker-compose up -d`

### 3. Redis 연결 실패

```bash
# Redis 컨테이너 로그 확인
docker-compose logs redis

# Redis 연결 테스트
docker exec -it insight_redis redis-cli ping
```

### 4. 파일 업로드 실패

```bash
# uploads 폴더 권한 확인
docker exec -it insight_app ls -la /app/uploads

# 권한 수정 (필요 시)
docker exec -it insight_app chmod -R 755 /app/uploads
```

### 5. 메모리 부족

```yaml
# docker-compose.yml에서 메모리 제한 완화
services:
  app:
    deploy:
      resources:
        limits:
          memory: 4G  # 2G → 4G로 증가
```

---

## 🔐 보안 권장사항

### 1. Secret Key 강화

```bash
# 강력한 Secret Key 생성
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### 2. 비root 사용자 실행

Dockerfile에서 이미 비root 사용자(`insight`)로 실행되도록 설정되어 있습니다.

### 3. 포트 노출 최소화

프로덕션 환경에서는 Nginx를 통해 접근하도록 설정:

```bash
# nginx 포함하여 실행
docker-compose --profile with-nginx up -d
```

### 4. HTTPS 설정

Nginx에 SSL 인증서 설정:

```nginx
# nginx/conf.d/default.conf
server {
    listen 443 ssl;
    server_name yourdomain.com;

    ssl_certificate /etc/nginx/ssl/cert.pem;
    ssl_certificate_key /etc/nginx/ssl/key.pem;

    location / {
        proxy_pass http://app:8080;
    }
}
```

---

## 📈 성능 최적화

### 1. Gunicorn 워커 최적화

**동시 사용자 예상 수에 따른 권장 설정:**

| 동시 사용자 | Workers | Worker Class | 메모리  |
|---------|---------|--------------|-------|
| ~10명    | 4       | sync         | 1GB   |
| ~50명    | 8       | gevent       | 2GB   |
| ~100명   | 16      | gevent       | 4GB   |

### 2. Redis 최적화

```env
# Redis 메모리 정책
REDIS_MAXMEMORY=256mb
REDIS_POLICY=allkeys-lru
```

### 3. MariaDB 최적화

```yaml
services:
  db:
    command: >
      --max_connections=200
      --innodb_buffer_pool_size=512M
      --query_cache_size=32M
```

---

## 🔄 데이터 백업

### 데이터베이스 백업

```bash
# 백업 생성
docker exec insight_db mysqldump -u root -p${DB_ROOT_PASSWORD} mbizsquare > backup.sql

# 복원
docker exec -i insight_db mysql -u root -p${DB_ROOT_PASSWORD} mbizsquare < backup.sql
```

### Redis 데이터 백업

```bash
# RDB 파일 복사
docker cp insight_redis:/data/dump.rdb ./redis_backup.rdb

# 복원
docker cp ./redis_backup.rdb insight_redis:/data/dump.rdb
docker-compose restart redis
```

### 파일 업로드 백업

```bash
# uploads 폴더 백업
docker cp insight_app:/app/uploads ./uploads_backup

# 복원
docker cp ./uploads_backup insight_app:/app/uploads
```

---

## 📝 환경 변수 전체 목록

| 변수명 | 기본값 | 설명 |
|--------|--------|------|
| `FLASK_ENV` | `production` | Flask 환경 (development/production) |
| `SECRET_KEY` | **필수** | Flask Secret Key |
| `JWT_SECRET_KEY` | **필수** | JWT Secret Key |
| `DB_ROOT_PASSWORD` | **필수** | MariaDB Root 비밀번호 |
| `DB_NAME` | `mbizsquare` | 데이터베이스 이름 |
| `DB_USER` | `insight_user` | 데이터베이스 사용자 |
| `DB_PASSWORD` | **필수** | 데이터베이스 비밀번호 |
| `OPENAI_API_KEY` | - | OpenAI API 키 |
| `AI_INSIGHTS_ENABLED` | `true` | AI 인사이트 활성화 |
| `GUNICORN_WORKERS` | `4` | Gunicorn 워커 수 |
| `GUNICORN_TIMEOUT` | `120` | 요청 타임아웃 (초) |
| `GUNICORN_WORKER_CLASS` | `sync` | 워커 클래스 (sync/gevent) |
| `SESSION_TYPE` | `redis` | 세션 타입 |
| `REDIS_URL` | `redis://redis:6379/0` | Redis 연결 URL |

---

## 🎓 추가 리소스

- [Docker 공식 문서](https://docs.docker.com/)
- [Docker Compose 문서](https://docs.docker.com/compose/)
- [Gunicorn 설정 가이드](https://docs.gunicorn.org/en/stable/settings.html)
- [Flask 프로덕션 배포](https://flask.palletsprojects.com/en/latest/deploying/)

---

## 💡 문제 해결 연락처

문제가 발생하면 다음 정보와 함께 문의하세요:

1. Docker 버전: `docker --version`
2. Docker Compose 버전: `docker-compose --version`
3. 로그 파일: `docker-compose logs > logs.txt`
4. 환경 변수 (민감 정보 제외)

---

**⚠️ 주의사항:**
- 프로덕션 배포 전 반드시 `.env` 파일의 모든 Secret Key를 변경하세요
- 정기적으로 데이터베이스와 파일을 백업하세요
- 로그를 모니터링하여 이상 징후를 조기에 발견하세요
