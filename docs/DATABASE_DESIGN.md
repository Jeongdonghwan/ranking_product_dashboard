# 데이터베이스 설계

## 개요

MariaDB를 사용하며, 기존 `users` 테이블을 참조하는 4개의 새로운 테이블을 생성합니다.

**주요 특징:**
- user_id: `VARCHAR(20)` (기존 users 테이블 구조 반영)
- utf8mb4 문자 인코딩 (한글 지원)
- JSON 컬럼 활용 (metrics_summary)
- 복합 인덱스로 쿼리 최적화
- CASCADE 삭제로 데이터 무결성 유지

---

## ERD (Entity Relationship Diagram)

```
┌────────────────────────┐
│        users           │ (기존 테이블)
├────────────────────────┤
│ PK  user_id VARCHAR(20)│
│     user_pw            │
│     user_nm            │
│     user_email         │
│     ...                │
└──────────┬─────────────┘
           │
           │ 1:N
           ↓
┌───────────────────────────────────────┐
│    ad_analysis_snapshots              │
├───────────────────────────────────────┤
│ PK  id INT AUTO_INCREMENT             │
│ FK  user_id VARCHAR(20)               │◄───────┐
│     snapshot_name VARCHAR(255)        │        │
│     period_start DATE                 │        │
│     period_end DATE                   │        │
│     data_json TEXT                    │        │
│     metrics_summary JSON              │        │
│     ai_insights TEXT                  │        │
│     created_at TIMESTAMP              │        │
│     updated_at TIMESTAMP              │        │
│     is_saved BOOLEAN                  │        │
│     tags VARCHAR(255)                 │        │
│     memo TEXT                         │        │
└──────────┬────────────────────────────┘        │
           │                                     │
           │ 1:N                                 │
           ↓                                     │
┌───────────────────────────────────────┐        │
│        ad_daily_data                  │        │
├───────────────────────────────────────┤        │
│ PK  id INT AUTO_INCREMENT             │        │
│ FK  snapshot_id INT                   │        │
│     date DATE                         │        │
│     campaign_name VARCHAR(255)        │        │
│     spend DECIMAL(12,2)               │        │
│     impressions INT                   │        │
│     clicks INT                        │        │
│     conversions INT                   │        │
│     revenue DECIMAL(12,2)             │        │
└───────────────────────────────────────┘        │
                                                  │
                                                  │
                                                  │ FK
┌───────────────────────────────────────┐        │
│      ad_campaign_memos                │        │
├───────────────────────────────────────┤        │
│ PK  id INT AUTO_INCREMENT             │        │
│ FK  user_id VARCHAR(20)               │────────┤
│     campaign_name VARCHAR(255)        │        │
│     memo TEXT                         │        │
│     created_at TIMESTAMP              │        │
└───────────────────────────────────────┘        │
                                                  │
                                                  │
┌───────────────────────────────────────┐        │
│       ad_monthly_goals                │        │
├───────────────────────────────────────┤        │
│ PK  id INT AUTO_INCREMENT             │        │
│ FK  user_id VARCHAR(20)               │────────┘
│     year_month VARCHAR(7)             │
│     budget DECIMAL(12,2)              │
│     target_roas DECIMAL(5,2)          │
│     target_revenue DECIMAL(12,2)      │
│ UK  (user_id, year_month)             │
└───────────────────────────────────────┘
```

---

## 테이블 상세 설계

### 1. ad_analysis_snapshots (분석 스냅샷)

**용도**: 광고 분석 세션 및 결과 저장

```sql
CREATE TABLE ad_analysis_snapshots (
    id INT PRIMARY KEY AUTO_INCREMENT COMMENT '스냅샷 ID',
    user_id VARCHAR(20) NOT NULL COMMENT '사용자 ID',
    snapshot_name VARCHAR(255) NOT NULL COMMENT '분석 이름',
    period_start DATE NOT NULL COMMENT '분석 시작일',
    period_end DATE NOT NULL COMMENT '분석 종료일',
    data_json TEXT NOT NULL COMMENT '원본 데이터 (JSON)',
    metrics_summary JSON COMMENT '계산된 지표 (캐싱)',
    ai_insights TEXT COMMENT 'AI 생성 인사이트',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '생성일시',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '수정일시',
    is_saved BOOLEAN DEFAULT FALSE COMMENT '사용자 저장 여부',
    tags VARCHAR(255) COMMENT '태그 (쉼표 구분)',
    memo TEXT COMMENT '사용자 메모',

    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    INDEX idx_user_date (user_id, period_start, period_end),
    INDEX idx_saved (user_id, is_saved),
    INDEX idx_created (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='광고 분석 스냅샷 저장';
```

**컬럼 설명**:
- `data_json`: pandas DataFrame을 JSON으로 변환한 원본 데이터
- `metrics_summary`: 계산된 모든 지표 (ROAS, CTR 등) - 빠른 조회용
- `is_saved`: false는 임시 분석, true는 사용자가 저장한 분석
- `tags`: 사용자 정의 태그 (예: "블프,신규캠페인")

**예시 데이터**:
| id | user_id | snapshot_name | period_start | period_end | is_saved | tags |
|----|---------|---------------|--------------|------------|----------|------|
| 1 | user123 | 11월 1주차 | 2024-11-04 | 2024-11-10 | true | 블프,신규 |
| 2 | user123 | 11월 2주차 | 2024-11-11 | 2024-11-17 | true | 블프 |
| 3 | user456 | 테스트 | 2024-11-01 | 2024-11-03 | false | |

---

### 2. ad_daily_data (일별 광고 데이터)

**용도**: 스냅샷의 일별 상세 데이터 저장

```sql
CREATE TABLE ad_daily_data (
    id INT PRIMARY KEY AUTO_INCREMENT COMMENT '데이터 ID',
    snapshot_id INT NOT NULL COMMENT '스냅샷 ID',
    date DATE NOT NULL COMMENT '날짜',
    campaign_name VARCHAR(255) NOT NULL COMMENT '캠페인명',
    spend DECIMAL(12, 2) NOT NULL COMMENT '지출액 (원)',
    impressions INT DEFAULT 0 COMMENT '노출수',
    clicks INT DEFAULT 0 COMMENT '클릭수',
    conversions INT DEFAULT 0 COMMENT '전환수',
    revenue DECIMAL(12, 2) DEFAULT 0 COMMENT '매출액 (원)',

    FOREIGN KEY (snapshot_id) REFERENCES ad_analysis_snapshots(id) ON DELETE CASCADE,
    INDEX idx_snapshot_date (snapshot_id, date),
    INDEX idx_campaign (campaign_name),
    INDEX idx_date (date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='일별 광고 데이터';
```

**컬럼 설명**:
- `spend`: 해당 일자+캠페인의 광고 지출액
- `impressions`: 광고 노출 횟수 (선택적, 기본값 0)
- `clicks`: 광고 클릭 횟수
- `conversions`: 전환(구매) 횟수
- `revenue`: 해당 전환으로 발생한 매출

**예시 데이터**:
| id | snapshot_id | date | campaign_name | spend | impressions | clicks | conversions | revenue |
|----|-------------|------|---------------|-------|-------------|--------|-------------|---------|
| 1 | 1 | 2024-11-04 | 블프_신규 | 150000 | 45000 | 1200 | 48 | 540000 |
| 2 | 1 | 2024-11-04 | 기존고객_A | 80000 | 20000 | 800 | 30 | 360000 |
| 3 | 1 | 2024-11-05 | 블프_신규 | 160000 | 48000 | 1300 | 52 | 580000 |

---

### 3. ad_campaign_memos (캠페인 메모)

**용도**: 특정 캠페인에 대한 사용자 메모 저장

```sql
CREATE TABLE ad_campaign_memos (
    id INT PRIMARY KEY AUTO_INCREMENT COMMENT '메모 ID',
    user_id VARCHAR(20) NOT NULL COMMENT '사용자 ID',
    campaign_name VARCHAR(255) NOT NULL COMMENT '캠페인명',
    memo TEXT NOT NULL COMMENT '메모 내용',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '작성일시',

    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    INDEX idx_user_campaign (user_id, campaign_name),
    INDEX idx_created (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='캠페인 메모';
```

**컬럼 설명**:
- `campaign_name`: 메모 대상 캠페인명
- `memo`: 사용자가 작성한 메모 (예: "소재 #3으로 교체", "타겟팅 범위 확대")

**예시 데이터**:
| id | user_id | campaign_name | memo | created_at |
|----|---------|---------------|------|------------|
| 1 | user123 | 블프_신규 | 소재 #3으로 교체 | 2024-11-10 14:30:00 |
| 2 | user123 | 블프_신규 | 타겟팅 범위 확대 | 2024-11-12 09:15:00 |
| 3 | user123 | 기존고객_A | 입찰가 10% 인상 | 2024-11-13 16:45:00 |

---

### 4. ad_monthly_goals (월별 목표)

**용도**: 월별 예산 및 목표 ROAS 저장

```sql
CREATE TABLE ad_monthly_goals (
    id INT PRIMARY KEY AUTO_INCREMENT COMMENT '목표 ID',
    user_id VARCHAR(20) NOT NULL COMMENT '사용자 ID',
    year_month VARCHAR(7) NOT NULL COMMENT '대상 월 (YYYY-MM)',
    budget DECIMAL(12, 2) COMMENT '월 예산 (원)',
    target_roas DECIMAL(5, 2) COMMENT '목표 ROAS',
    target_revenue DECIMAL(12, 2) COMMENT '목표 매출 (원)',

    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    UNIQUE KEY uk_user_month (user_id, year_month),
    INDEX idx_year_month (year_month)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='월별 목표 설정';
```

**컬럼 설명**:
- `year_month`: YYYY-MM 형식 (예: "2024-11")
- `budget`: 해당 월의 총 광고 예산
- `target_roas`: 목표 ROAS (예: 4.0 = 광고비 대비 4배 매출)
- `target_revenue`: 목표 매출액

**Unique Key**: (user_id, year_month) - 한 사용자는 한 달에 하나의 목표만 설정 가능

**예시 데이터**:
| id | user_id | year_month | budget | target_roas | target_revenue |
|----|---------|------------|--------|-------------|----------------|
| 1 | user123 | 2024-11 | 10000000 | 4.0 | 40000000 |
| 2 | user123 | 2024-12 | 12000000 | 4.2 | 50400000 |
| 3 | user456 | 2024-11 | 5000000 | 3.5 | 17500000 |

---

## 인덱스 전략

### 1. Primary Key 인덱스
모든 테이블에 `AUTO_INCREMENT` PK 사용 - 빠른 조회 및 관계 설정

### 2. Foreign Key 인덱스
외래키는 자동으로 인덱스 생성 - JOIN 성능 향상

### 3. 복합 인덱스

**ad_analysis_snapshots**:
- `idx_user_date (user_id, period_start, period_end)`: 사용자별 기간 검색
- `idx_saved (user_id, is_saved)`: 저장된 분석 필터링

**ad_daily_data**:
- `idx_snapshot_date (snapshot_id, date)`: 스냅샷별 일별 데이터 조회
- `idx_campaign (campaign_name)`: 캠페인별 집계

**ad_campaign_memos**:
- `idx_user_campaign (user_id, campaign_name)`: 특정 캠페인 메모 조회

**ad_monthly_goals**:
- `uk_user_month (user_id, year_month)`: UNIQUE 제약 + 빠른 조회

---

## 쿼리 예시

### 1. 사용자의 저장된 분석 목록 조회
```sql
SELECT
    id,
    snapshot_name,
    period_start,
    period_end,
    tags,
    memo,
    created_at,
    JSON_EXTRACT(metrics_summary, '$.avg_roas') as avg_roas,
    JSON_EXTRACT(metrics_summary, '$.total_spend') as total_spend
FROM ad_analysis_snapshots
WHERE user_id = 'user123'
  AND is_saved = TRUE
ORDER BY created_at DESC;
```

### 2. 특정 스냅샷의 일별 데이터 조회
```sql
SELECT
    date,
    campaign_name,
    spend,
    revenue,
    clicks,
    conversions,
    ROUND(revenue / spend, 2) as roas,
    ROUND(conversions / clicks * 100, 2) as cvr
FROM ad_daily_data
WHERE snapshot_id = 123
ORDER BY date, campaign_name;
```

### 3. 캠페인별 총 지표 (특정 스냅샷)
```sql
SELECT
    campaign_name,
    SUM(spend) as total_spend,
    SUM(revenue) as total_revenue,
    SUM(clicks) as total_clicks,
    SUM(conversions) as total_conversions,
    SUM(impressions) as total_impressions,
    ROUND(SUM(revenue) / SUM(spend), 2) as roas,
    ROUND(SUM(clicks) / SUM(impressions) * 100, 2) as ctr,
    ROUND(SUM(spend) / SUM(conversions), 0) as cpa
FROM ad_daily_data
WHERE snapshot_id = 123
GROUP BY campaign_name
ORDER BY roas DESC;
```

### 4. 월별 예산 소진 현황
```sql
SELECT
    g.budget,
    g.target_roas,
    COALESCE(SUM(d.spend), 0) as spent,
    ROUND(COALESCE(SUM(d.spend), 0) / g.budget * 100, 1) as spent_rate
FROM ad_monthly_goals g
LEFT JOIN ad_analysis_snapshots s ON g.user_id = s.user_id
LEFT JOIN ad_daily_data d ON s.id = d.snapshot_id
WHERE g.user_id = 'user123'
  AND g.year_month = '2024-11'
  AND DATE_FORMAT(d.date, '%Y-%m') = '2024-11'
GROUP BY g.id;
```

### 5. 기간 비교 (두 스냅샷)
```sql
-- 스냅샷 A의 지표
SELECT
    JSON_EXTRACT(metrics_summary, '$.avg_roas') as roas_a
FROM ad_analysis_snapshots
WHERE id = 124;

-- 스냅샷 B의 지표
SELECT
    JSON_EXTRACT(metrics_summary, '$.avg_roas') as roas_b
FROM ad_analysis_snapshots
WHERE id = 123;

-- Python에서 변화율 계산
```

---

## 데이터 무결성

### CASCADE 삭제
```sql
-- 스냅샷 삭제 시 연관된 일별 데이터도 자동 삭제
DELETE FROM ad_analysis_snapshots WHERE id = 123;
-- → ad_daily_data의 snapshot_id=123 레코드도 자동 삭제
```

### 외래키 제약
- 존재하지 않는 user_id로 데이터 생성 불가
- 존재하지 않는 snapshot_id로 일별 데이터 생성 불가

### UNIQUE 제약
- 한 사용자는 한 달에 하나의 목표만 설정 가능
- 중복 저장 시 UPDATE 처리 (UPSERT)

---

## 스토리지 추정

### 1. ad_analysis_snapshots
- 평균 레코드 크기: ~5KB (data_json 포함)
- 사용자당 월 10개 분석 생성 가정
- 100명 사용자 × 10개/월 × 12개월 = 12,000개
- 예상 용량: 60MB

### 2. ad_daily_data
- 평균 레코드 크기: ~200 bytes
- 분석당 30일 × 5개 캠페인 = 150개 레코드
- 12,000개 분석 × 150개 = 1,800,000개
- 예상 용량: 360MB

### 3. ad_campaign_memos
- 평균 레코드 크기: ~500 bytes
- 사용자당 월 10개 메모 가정
- 100명 × 10개/월 × 12개월 = 12,000개
- 예상 용량: 6MB

### 4. ad_monthly_goals
- 평균 레코드 크기: ~100 bytes
- 100명 × 12개월 = 1,200개
- 예상 용량: 120KB

**총 예상 용량 (연간)**: ~430MB

---

## 백업 전략

### 1. 일일 전체 백업
```bash
mysqldump -u user -p mbizsquare \
  ad_analysis_snapshots \
  ad_daily_data \
  ad_campaign_memos \
  ad_monthly_goals \
  > backup_$(date +%Y%m%d).sql
```

### 2. 복구
```bash
mysql -u user -p mbizsquare < backup_20241115.sql
```

---

## 마이그레이션 스크립트

### 초기 테이블 생성
```bash
mysql -u root -p mbizsquare < database/schema.sql
```

### 기존 데이터가 있을 경우
```sql
-- 테이블 존재 확인
SHOW TABLES LIKE 'ad_%';

-- 데이터 백업 후 재생성
DROP TABLE IF EXISTS ad_daily_data;
DROP TABLE IF EXISTS ad_campaign_memos;
DROP TABLE IF EXISTS ad_monthly_goals;
DROP TABLE IF EXISTS ad_analysis_snapshots;

-- schema.sql 실행
SOURCE database/schema.sql;
```

---

## 성능 튜닝

### 1. JSON 컬럼 최적화
```sql
-- JSON 경로 인덱싱 (MySQL 5.7+)
ALTER TABLE ad_analysis_snapshots
ADD COLUMN roas_cached DECIMAL(5,2)
  GENERATED ALWAYS AS (JSON_EXTRACT(metrics_summary, '$.avg_roas')) STORED;

CREATE INDEX idx_roas ON ad_analysis_snapshots(roas_cached);
```

### 2. 파티셔닝 (대용량 데이터)
```sql
-- 날짜별 파티셔닝 (월 1,000,000+ 레코드 시)
ALTER TABLE ad_daily_data
PARTITION BY RANGE (YEAR(date) * 100 + MONTH(date)) (
    PARTITION p202401 VALUES LESS THAN (202402),
    PARTITION p202402 VALUES LESS THAN (202403),
    -- ...
);
```

### 3. 쿼리 최적화
```sql
-- EXPLAIN으로 쿼리 플랜 확인
EXPLAIN SELECT * FROM ad_daily_data WHERE snapshot_id = 123;

-- 인덱스 사용 확인
SHOW INDEX FROM ad_daily_data;
```

---

## 참고 자료

- [MariaDB JSON 데이터 타입](https://mariadb.com/kb/en/json-data-type/)
- [인덱스 최적화](https://mariadb.com/kb/en/getting-the-best-use-of-indexes/)
- [외래키 제약](https://mariadb.com/kb/en/foreign-keys/)
