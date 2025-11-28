# 알려진 이슈 및 해결 방법

## 개요

이 문서는 광고 분석 대시보드 개발 및 운영 중 발견된 제약사항, 알려진 이슈, 그리고 해결 방법을 정리합니다.

---

## 1. 인증 및 세션

### Issue #1: JWT 토큰 만료로 인한 접근 차단

**문제**:
- JWT 토큰의 만료 시간이 5분으로 설정되어 있어, 링크 클릭 후 5분이 지나면 접근 불가

**재현 방법**:
1. 메인 사이트에서 광고분석 링크 클릭
2. URL 복사
3. 5분 후 해당 URL 접속 시도

**해결 방법**:
- JWT는 첫 접속용이므로 문제없음
- 이후 접속은 Flask 세션 쿠키 사용
- 세션 만료 시 메인 사이트 로그인으로 자동 리다이렉트

**Status**: Not a Bug (설계된 동작)

---

### Issue #2: 세션 파일 저장소 디스크 공간

**문제**:
- Flask 파일 기반 세션은 `flask_session/` 디렉토리에 파일로 저장
- 사용자 수가 많아지면 디스크 공간 사용 증가

**예상 용량**:
- 세션당 약 1KB
- 1,000명 동시 사용자 = 1MB

**해결 방법**:
1. **단기**: 주기적 세션 파일 정리
```python
# 만료된 세션 파일 자동 삭제
from datetime import datetime, timedelta
import os

def clean_expired_sessions():
    session_dir = 'flask_session'
    expire_time = datetime.now() - timedelta(hours=1)

    for filename in os.listdir(session_dir):
        filepath = os.path.join(session_dir, filename)
        if os.path.getmtime(filepath) < expire_time.timestamp():
            os.remove(filepath)
```

2. **장기**: Redis 세션 스토어로 전환
```python
app.config['SESSION_TYPE'] = 'redis'
app.config['SESSION_REDIS'] = Redis(host='localhost', port=6379)
```

**Status**: Workaround Available

---

### Issue #3: 크로스 도메인 세션 공유 불가

**문제**:
- 메인 사이트(`mbizsquare.com`)와 Insight 앱(`ad-insight.mbizsquare.com`)이 다른 도메인인 경우 세션 쿠키 공유 불가

**영향**:
- 사용자가 매번 JWT 토큰으로 인증해야 함

**해결 방법**:
- 현재 JWT 방식으로 해결됨
- 향후 같은 서브도메인 사용 시 쿠키 도메인 설정:
```python
app.config['SESSION_COOKIE_DOMAIN'] = '.mbizsquare.com'
```

**Status**: Won't Fix (설계대로)

---

## 2. 파일 업로드

### Issue #4: 대용량 파일 업로드 시간 초과

**문제**:
- 10MB 파일 업로드 시 pandas 처리에 시간이 걸려 브라우저 타임아웃 발생 가능

**재현 방법**:
1. 10MB 크기의 CSV 파일 (10만 행) 업로드
2. 파일 파싱 + DB 저장에 30초 이상 소요
3. 브라우저 30초 타임아웃 발생

**해결 방법**:
1. **Gunicorn 타임아웃 증가** (현재: 120초)
```python
# run.py
gunicorn --timeout 120 run:app
```

2. **프로그레스 바 표시**
```javascript
// 프론트엔드에서 업로드 진행 상태 표시
const xhr = new XMLHttpRequest();
xhr.upload.addEventListener('progress', (e) => {
    const percent = (e.loaded / e.total) * 100;
    updateProgressBar(percent);
});
```

3. **비동기 처리** (추후 도입)
- Celery로 백그라운드 작업
- 업로드 즉시 202 Accepted 응답
- 작업 완료 시 알림

**Status**: Workaround Available

---

### Issue #5: 파일 삭제 실패 시 디스크 공간 누적

**문제**:
- 파일 처리 후 자동 삭제하지만, 에러 발생 시 파일이 남을 수 있음

**해결 방법**:
1. **Try-Finally 블록 사용**
```python
@app.route('/api/ad-analysis/upload', methods=['POST'])
def upload_data():
    file_path = None
    try:
        file_path = os.path.join('uploads', secure_filename(file.filename))
        file.save(file_path)

        # 처리 로직

    finally:
        if file_path and os.path.exists(file_path):
            os.remove(file_path)  # 반드시 삭제
```

2. **크론 작업으로 주기적 정리**
```bash
# 1시간 이상 된 파일 삭제
0 * * * * find /app/uploads -type f -mmin +60 -delete
```

**Status**: Fixed

---

### Issue #6: 파일 확장자 위장 공격

**문제**:
- 악의적 사용자가 `.xlsx` 확장자로 실행 파일 업로드 시도

**재현 방법**:
1. 악성 스크립트를 `malware.exe`로 생성
2. 파일명을 `data.xlsx`로 변경
3. 업로드 시도

**해결 방법**:
1. **파일 확장자 + MIME 타입 검증**
```python
from werkzeug.utils import secure_filename
import magic

ALLOWED_EXTENSIONS = {'xlsx', 'xls', 'csv'}
ALLOWED_MIMES = {
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    'application/vnd.ms-excel',
    'text/csv'
}

def allowed_file(file):
    # 확장자 검증
    if '.' not in file.filename:
        return False
    ext = file.filename.rsplit('.', 1)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        return False

    # MIME 타입 검증
    mime = magic.from_buffer(file.read(1024), mime=True)
    file.seek(0)  # 파일 포인터 리셋

    return mime in ALLOWED_MIMES
```

2. **pandas 예외 처리**
- 실제 Excel/CSV가 아니면 pandas에서 에러 발생
- 에러 발생 시 파일 즉시 삭제

**Status**: Fixed

---

## 3. 데이터베이스

### Issue #7: JSON 컬럼의 쿼리 성능 저하

**문제**:
- `metrics_summary` JSON 컬럼 검색 시 인덱스 사용 불가

**재현 방법**:
```sql
SELECT * FROM ad_analysis_snapshots
WHERE JSON_EXTRACT(metrics_summary, '$.avg_roas') > 3.5;
-- Full Table Scan 발생
```

**해결 방법**:
1. **Generated Column 사용** (MariaDB 10.2+)
```sql
ALTER TABLE ad_analysis_snapshots
ADD COLUMN roas_cached DECIMAL(5,2)
  GENERATED ALWAYS AS (JSON_EXTRACT(metrics_summary, '$.avg_roas')) STORED;

CREATE INDEX idx_roas ON ad_analysis_snapshots(roas_cached);
```

2. **애플리케이션 레벨 필터링**
- DB에서 전체 데이터 가져온 후 Python에서 필터링

**Status**: Workaround Available

---

### Issue #8: user_id VARCHAR(20) vs INT 혼동

**문제**:
- CLAUDE.md 초기 버전에서 `user_id INT` 로 설계
- 실제 users 테이블은 `user_id VARCHAR(20)`

**영향**:
- 외래키 타입 불일치로 테이블 생성 실패

**해결 방법**:
- 모든 테이블의 `user_id`를 `VARCHAR(20)`으로 수정 완료

**Status**: Fixed

---

### Issue #9: 연결 풀 고갈

**문제**:
- 동시 요청 증가 시 MariaDB 연결 풀 고갈

**증상**:
```
pymysql.err.OperationalError: (2003, "Can't connect to MySQL server")
```

**해결 방법**:
1. **연결 풀 크기 증가**
```python
pool = pymysql.pooling.PooledDB(
    creator=pymysql,
    maxconnections=20,  # 기본값 0 → 20으로 증가
    mincached=5,
    maxcached=10,
    blocking=True
)
```

2. **연결 재사용 확인**
```python
def execute_query(sql, params):
    conn = pool.connection()
    try:
        cursor = conn.cursor()
        cursor.execute(sql, params)
        result = cursor.fetchall()
        return result
    finally:
        cursor.close()
        conn.close()  # 풀에 반환
```

**Status**: Fixed

---

## 4. AI 통합

### Issue #10: OpenAI API 비용 급증

**문제**:
- 사용자가 여러 번 파일 업로드 시 GPT-4 API 비용 증가
- GPT-4 비용: $0.03/1K tokens (input), $0.06/1K tokens (output)
- 평균 요청당 약 2,000 tokens = $0.12

**예상 월간 비용**:
- 100명 사용자 × 월 20회 업로드 = 2,000 요청
- 2,000 × $0.12 = $240/월

**해결 방법**:
1. **AI 인사이트 선택적 활성화** (구현 완료)
```python
# .env
AI_INSIGHTS_ENABLED=false
```

2. **인사이트 캐싱**
- 동일 데이터에 대해 AI 재요청 방지
```python
if snapshot.ai_insights:
    return snapshot.ai_insights  # 캐시된 인사이트 반환
```

3. **사용량 제한**
- 사용자당 일 10회 제한
- Rate Limiting 도입

**Status**: Workaround Available

---

### Issue #11: OpenAI API 응답 지연

**문제**:
- GPT-4 API 응답 시간: 평균 5-10초
- 사용자가 업로드 후 오래 기다려야 함

**해결 방법**:
1. **비동기 처리**
```python
# 업로드 즉시 응답, AI는 백그라운드에서 처리
{
  "success": true,
  "snapshot_id": 123,
  "metrics": {...},
  "insights": "AI 인사이트 생성 중..."  # 임시 메시지
}

# Celery 작업으로 AI 생성 후 DB 업데이트
```

2. **스트리밍 응답** (SSE)
- Server-Sent Events로 AI 응답 실시간 표시

**Status**: Enhancement (추후 도입)

---

### Issue #12: OpenAI API 에러 처리

**문제**:
- API 키 없음, 할당량 초과, 네트워크 오류 시 전체 업로드 실패

**해결 방법**:
```python
def generate_insights(self, metrics, df):
    if not self.enabled:
        return "AI 인사이트가 비활성화되어 있습니다."

    try:
        response = openai.ChatCompletion.create(...)
        return response.choices[0].message.content
    except openai.error.AuthenticationError:
        return "AI API 키가 유효하지 않습니다."
    except openai.error.RateLimitError:
        return "AI API 할당량을 초과했습니다. 나중에 다시 시도해주세요."
    except Exception as e:
        logger.error(f"AI 인사이트 생성 실패: {e}")
        return "AI 인사이트 생성 중 오류가 발생했습니다."
```

**Status**: Fixed

---

## 5. 프론트엔드

### Issue #13: Chart.js 한글 폰트 깨짐

**문제**:
- Chart.js 기본 폰트로 한글 렌더링 시 깨짐

**해결 방법**:
```javascript
Chart.defaults.font.family = "'Noto Sans KR', sans-serif";

// 또는 개별 차트 설정
const chartOptions = {
    plugins: {
        legend: {
            labels: {
                font: {
                    family: "'Noto Sans KR', sans-serif"
                }
            }
        }
    }
};
```

**Status**: Fixed

---

### Issue #14: 드래그 앤 드롭이 파이어폭스에서 작동 안 함

**문제**:
- Firefox에서 드래그 앤 드롭 이벤트 미발생

**해결 방법**:
```javascript
uploadArea.addEventListener('dragover', (e) => {
    e.preventDefault();  // 필수!
    e.stopPropagation();
});

uploadArea.addEventListener('drop', (e) => {
    e.preventDefault();  // 필수!
    e.stopPropagation();

    const files = e.dataTransfer.files;
    if (files.length > 0) {
        uploadFile(files[0]);
    }
});
```

**Status**: Fixed

---

### Issue #15: 차트 반응형 깨짐

**문제**:
- 브라우저 크기 조정 시 차트 비율 깨짐

**해결 방법**:
```javascript
const chartOptions = {
    responsive: true,
    maintainAspectRatio: false  // 컨테이너 높이 유지
};

// CSS에서 컨테이너 높이 고정
.chart-container {
    position: relative;
    height: 400px;
}
```

**Status**: Fixed

---

## 6. 배포 및 운영

### Issue #16: Docker 컨테이너 재시작 시 세션 손실

**문제**:
- 파일 기반 세션은 컨테이너 재시작 시 손실

**해결 방법**:
1. **볼륨 마운트**
```yaml
# docker-compose.yml
volumes:
  - ./flask_session:/app/flask_session
```

2. **Redis 세션 사용** (권장)
```yaml
services:
  redis:
    image: redis:alpine

  ad-insight:
    environment:
      - SESSION_TYPE=redis
      - SESSION_REDIS_URL=redis://redis:6379
```

**Status**: Workaround Available

---

### Issue #17: 로그 파일 크기 무제한 증가

**문제**:
- 운영 환경에서 로그 파일이 계속 커짐

**해결 방법**:
```python
import logging
from logging.handlers import RotatingFileHandler

handler = RotatingFileHandler(
    'app.log',
    maxBytes=10*1024*1024,  # 10MB
    backupCount=5
)

app.logger.addHandler(handler)
```

**Status**: Fixed

---

### Issue #18: HTTPS 없이 배포 시 쿠키 전송 안 됨

**문제**:
- 프로덕션 환경에서 `SESSION_COOKIE_SECURE=True` 설정 시 HTTP에서 쿠키 전송 안 됨

**해결 방법**:
1. **HTTPS 필수**
- Let's Encrypt로 무료 SSL 인증서 발급
- Nginx에서 HTTPS 리다이렉트 설정

2. **개발 환경에서만 HTTP 허용**
```python
if app.config['ENV'] == 'production':
    app.config['SESSION_COOKIE_SECURE'] = True
else:
    app.config['SESSION_COOKIE_SECURE'] = False
```

**Status**: Configuration Required

---

## 7. 성능

### Issue #19: 10만 행 데이터 처리 시 메모리 부족

**문제**:
- 대용량 CSV 파일 업로드 시 pandas DataFrame이 메모리 초과

**해결 방법**:
1. **청크 처리**
```python
chunk_size = 10000
chunks = pd.read_csv(file_path, chunksize=chunk_size)

for chunk in chunks:
    # 청크별 DB 저장
    save_daily_data(chunk)
```

2. **파일 크기 제한 강화**
- 10MB → 5MB로 축소
- 또는 행 수 제한 (최대 50,000행)

**Status**: Enhancement (추후 도입)

---

### Issue #20: 동시 업로드 시 서버 과부하

**문제**:
- 여러 사용자가 동시에 대용량 파일 업로드 시 CPU 100%

**해결 방법**:
1. **Gunicorn Workers 증가**
```bash
gunicorn --workers 4 --threads 2 run:app
```

2. **Rate Limiting**
```python
from flask_limiter import Limiter

limiter = Limiter(app, key_func=get_remote_address)

@app.route('/api/ad-analysis/upload', methods=['POST'])
@limiter.limit("10 per minute")
def upload_data():
    ...
```

**Status**: Enhancement (추후 도입)

---

## 8. 데이터 정합성

### Issue #21: 날짜 형식 불일치

**문제**:
- Excel에서 날짜가 숫자 형식(44520)으로 저장된 경우 파싱 실패

**해결 방법**:
```python
def parse_date(date_value):
    if isinstance(date_value, str):
        return pd.to_datetime(date_value, format='%Y-%m-%d')
    elif isinstance(date_value, (int, float)):
        # Excel 날짜 숫자를 datetime으로 변환
        return pd.Timestamp('1899-12-30') + pd.Timedelta(days=date_value)
    else:
        return pd.to_datetime(date_value)

df['date'] = df['date'].apply(parse_date)
```

**Status**: Fixed

---

### Issue #22: 0으로 나누기 에러

**문제**:
- 클릭수가 0인 경우 CTR, CVR 계산 시 Division by zero

**해결 방법**:
```python
# 모든 계산에 0 체크 포함
avg_ctr = round((total_clicks / total_impressions * 100), 2) if total_impressions > 0 else 0
cvr = round((total_conversions / total_clicks * 100), 2) if total_clicks > 0 else 0
```

**Status**: Fixed

---

## 요약

| Category | Total Issues | Fixed | Workaround | Enhancement |
|----------|--------------|-------|------------|-------------|
| 인증/세션 | 3 | 0 | 2 | 1 |
| 파일 업로드 | 3 | 3 | 0 | 0 |
| 데이터베이스 | 3 | 2 | 1 | 0 |
| AI 통합 | 3 | 1 | 1 | 1 |
| 프론트엔드 | 3 | 3 | 0 | 0 |
| 배포/운영 | 3 | 2 | 1 | 0 |
| 성능 | 2 | 0 | 0 | 2 |
| 데이터 정합성 | 2 | 2 | 0 | 0 |
| **Total** | **22** | **13** | **5** | **4** |

---

## 추후 개선 계획

1. Redis 세션 스토어 전환
2. Celery 비동기 작업 처리
3. Rate Limiting 도입
4. 대용량 파일 청크 처리
5. 인사이트 캐싱 시스템
6. 모니터링 대시보드 (Prometheus + Grafana)

---

## 버그 리포트

새로운 이슈 발견 시:
1. GitHub Issues 등록
2. 재현 방법 상세히 기술
3. 환경 정보 포함 (OS, Python 버전, 브라우저)
