# 광고 분석 대시보드 - Dockerfile
# Python 3.10 기반 프로덕션 배포용

FROM python:3.10-slim

LABEL maintainer="insight-dashboard"
LABEL description="Advertisement Analytics Dashboard with Flask + Gunicorn"

# 작업 디렉토리 설정
WORKDIR /app

# 환경 변수 설정
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# 시스템 패키지 업데이트 및 필수 패키지 설치
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    default-libmysqlclient-dev \
    pkg-config \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Python 의존성 복사 및 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt \
    && pip install --no-cache-dir gunicorn gevent

# 애플리케이션 코드 복사
COPY . .

# 필요한 디렉토리 생성 및 권한 설정
RUN mkdir -p \
    /app/uploads \
    /var/log/insight \
    /app/flask_session \
    /app/app/static/uploads/banners \
    && chmod -R 755 /app/uploads /var/log/insight /app/flask_session \
    && chmod -R 755 /app/app/static/uploads/banners

# 비root 사용자 생성 (보안 강화)
RUN useradd -m -u 1000 insight && chown -R insight:insight /app /var/log/insight
USER insight

# 헬스체크
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# 포트 노출
EXPOSE 8080

# Gunicorn 실행
CMD ["gunicorn", "-c", "gunicorn.conf.py", "run:app"]
