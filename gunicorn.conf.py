# Gunicorn Configuration File
# 광고 분석 대시보드 - 프로덕션 배포용

import os
import multiprocessing

# ========================================
# Server Socket
# ========================================

# 바인드 주소 (Docker 컨테이너 내부에서는 0.0.0.0 사용)
bind = os.getenv('GUNICORN_BIND', '0.0.0.0:8080')

# Backlog (대기 큐 크기)
backlog = int(os.getenv('GUNICORN_BACKLOG', 2048))


# ========================================
# Worker Processes
# ========================================

# 워커 프로세스 수 (CPU 코어 * 2 + 1 권장)
# Docker 환경에서는 명시적으로 설정하거나 auto-detection 사용
workers = int(os.getenv('GUNICORN_WORKERS', multiprocessing.cpu_count() * 2 + 1))

# 워커 클래스
# sync: 기본 동기 워커 (간단하고 안정적)
# gevent: 비동기 워커 (더 많은 동시 연결 처리)
worker_class = os.getenv('GUNICORN_WORKER_CLASS', 'sync')

# 워커 연결 수 (gevent 사용 시)
worker_connections = int(os.getenv('GUNICORN_WORKER_CONNECTIONS', 1000))

# 워커 당 스레드 수 (sync 워커에서 threads 사용 시)
threads = int(os.getenv('GUNICORN_THREADS', 1))


# ========================================
# Timeouts
# ========================================

# 요청 타임아웃 (OpenAI API 호출 고려하여 120초로 설정)
timeout = int(os.getenv('GUNICORN_TIMEOUT', 120))

# Graceful timeout (워커 재시작 대기 시간)
graceful_timeout = int(os.getenv('GUNICORN_GRACEFUL_TIMEOUT', 30))

# Keep-alive connections
keepalive = int(os.getenv('GUNICORN_KEEPALIVE', 5))


# ========================================
# Worker Lifecycle
# ========================================

# 워커 자동 재시작 (메모리 누수 방지)
# 워커가 N개의 요청을 처리한 후 자동 재시작
max_requests = int(os.getenv('GUNICORN_MAX_REQUESTS', 1000))

# max_requests에 랜덤 지터 추가 (동시 재시작 방지)
max_requests_jitter = int(os.getenv('GUNICORN_MAX_REQUESTS_JITTER', 50))


# ========================================
# Server Mechanics
# ========================================

# 프리로드 (메모리 절약, 단 코드 변경 시 전체 재시작 필요)
preload_app = os.getenv('GUNICORN_PRELOAD', 'false').lower() == 'true'

# 데몬 모드 (백그라운드 실행)
daemon = False

# PID 파일
pidfile = os.getenv('GUNICORN_PID', None)

# 사용자/그룹 (보안 강화 시 사용)
user = os.getenv('GUNICORN_USER', None)
group = os.getenv('GUNICORN_GROUP', None)

# Temporary directory
tmp_upload_dir = None


# ========================================
# Logging
# ========================================

# 로그 레벨: debug, info, warning, error, critical
loglevel = os.getenv('GUNICORN_LOG_LEVEL', 'info')

# 액세스 로그 파일 경로
accesslog = os.getenv('GUNICORN_ACCESS_LOG', '/var/log/insight/gunicorn_access.log')

# 에러 로그 파일 경로
errorlog = os.getenv('GUNICORN_ERROR_LOG', '/var/log/insight/gunicorn_error.log')

# 액세스 로그 포맷
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# stdout/stderr로 로그 출력 (Docker 환경에서 유용)
# accesslog = '-'
# errorlog = '-'


# ========================================
# Process Naming
# ========================================

# 프로세스 이름 (ps aux에서 식별 용이)
proc_name = os.getenv('GUNICORN_PROC_NAME', 'insight-gunicorn')


# ========================================
# Server Hooks
# ========================================

def on_starting(server):
    """서버 시작 시 호출"""
    server.log.info("="*50)
    server.log.info("Gunicorn server starting...")
    server.log.info(f"Workers: {workers}")
    server.log.info(f"Worker class: {worker_class}")
    server.log.info(f"Timeout: {timeout}s")
    server.log.info(f"Bind: {bind}")
    server.log.info("="*50)


def on_reload(server):
    """코드 리로드 시 호출"""
    server.log.info("Reloading Gunicorn...")


def worker_int(worker):
    """워커가 SIGINT 받을 때 호출"""
    worker.log.info(f"Worker {worker.pid} interrupted")


def worker_abort(worker):
    """워커가 SIGABRT 받을 때 호출"""
    worker.log.info(f"Worker {worker.pid} aborted")


def pre_fork(server, worker):
    """워커 fork 전 호출"""
    pass


def post_fork(server, worker):
    """워커 fork 후 호출"""
    server.log.info(f"Worker spawned (pid: {worker.pid})")


def pre_exec(server):
    """새 마스터 프로세스로 exec 전 호출"""
    server.log.info("Forked child, re-executing.")


def when_ready(server):
    """서버가 요청을 받을 준비가 되었을 때 호출"""
    server.log.info("Server is ready. Spawning workers")


def worker_exit(server, worker):
    """워커 종료 시 호출"""
    server.log.info(f"Worker exited (pid: {worker.pid})")


def nworkers_changed(server, new_value, old_value):
    """워커 수 변경 시 호출"""
    server.log.info(f"Workers changed from {old_value} to {new_value}")


# ========================================
# SSL (HTTPS 사용 시)
# ========================================

# keyfile = '/path/to/keyfile'
# certfile = '/path/to/certfile'
# ca_certs = '/path/to/ca_certs'


# ========================================
# Environment Variables Override
# ========================================

# 환경변수로 설정 가능한 주요 옵션:
# - GUNICORN_WORKERS: 워커 수 (기본: CPU * 2 + 1)
# - GUNICORN_TIMEOUT: 타임아웃 초 (기본: 120)
# - GUNICORN_WORKER_CLASS: 워커 클래스 (기본: sync)
# - GUNICORN_BIND: 바인드 주소 (기본: 0.0.0.0:8080)
# - GUNICORN_LOG_LEVEL: 로그 레벨 (기본: info)

print(f"[Gunicorn Config] Workers={workers}, Class={worker_class}, Timeout={timeout}s, Bind={bind}")
