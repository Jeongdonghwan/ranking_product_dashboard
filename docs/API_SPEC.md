# API 명세서

## 기본 정보

- **Base URL**: `https://ad-insight.mbizsquare.com`
- **인증 방식**: Session Cookie (JWT로 최초 인증)
- **Content-Type**: `application/json` (파일 업로드 제외)
- **에러 응답 형식**: `{"error": "에러 메시지"}`

## 인증

모든 API는 세션 인증이 필요합니다. 세션이 없으면 `401 Unauthorized` 응답을 반환합니다.

```json
// 401 응답
{
  "error": "Unauthorized",
  "redirect": "https://mbizsquare.com/login"
}
```

---

## 1. 메인 페이지

### GET /

**설명**: JWT 토큰 검증 및 세션 생성 후 대시보드로 리다이렉트

**Query Parameters**:
| 파라미터 | 타입 | 필수 | 설명 |
|---------|------|------|------|
| token | string | No | JWT 인증 토큰 (첫 접속 시) |

**응답**:
- JWT 유효 → 302 Redirect `/ad-dashboard`
- 세션 있음 → 302 Redirect `/ad-dashboard`
- 둘 다 없음 → 302 Redirect `https://mbizsquare.com/login`

---

## 2. 대시보드 페이지

### GET /ad-dashboard

**설명**: 광고 분석 대시보드 HTML 페이지 반환

**인증**: 필수

**응답**: HTML 페이지

---

## 3. 파일 업로드

### POST /api/ad-analysis/upload

**설명**: Excel/CSV 파일 업로드 및 분석 실행

**인증**: 필수

**Content-Type**: `multipart/form-data`

**Request Body**:
| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| file | File | Yes | Excel/CSV 파일 (.xlsx, .xls, .csv) |
| snapshot_name | string | No | 분석 이름 (기본값: "분석 YYYY-MM-DD") |

**필수 컬럼** (Excel/CSV 내):
- `date`: 날짜 (YYYY-MM-DD)
- `campaign_name`: 캠페인명
- `spend`: 지출액 (숫자)
- `clicks`: 클릭수 (숫자)
- `conversions`: 전환수 (숫자)
- `revenue`: 매출액 (숫자)
- `impressions`: 노출수 (선택, 기본값 0)

**응답**: `200 OK`
```json
{
  "success": true,
  "snapshot_id": 123,
  "metrics": {
    "total_spend": 5800000,
    "total_revenue": 20300000,
    "total_clicks": 15400,
    "total_conversions": 420,
    "total_impressions": 520000,
    "avg_roas": 3.5,
    "avg_ctr": 2.96,
    "avg_cpc": 376,
    "avg_cpa": 13809,
    "cvr": 2.73,
    "avg_order_value": 48333,
    "campaigns": [
      {
        "campaign_name": "블프_신규",
        "rank": 1,
        "spend": 1200000,
        "revenue": 5400000,
        "clicks": 3200,
        "conversions": 108,
        "impressions": 120000,
        "roas": 4.5,
        "ctr": 2.67,
        "cpa": 11111,
        "cvr": 3.38,
        "status": "excellent"
      }
    ],
    "daily_trend": [
      {
        "date": "2024-01-01",
        "spend": 150000,
        "revenue": 540000,
        "clicks": 1200,
        "conversions": 48,
        "impressions": 45000,
        "roas": 3.6,
        "ctr": 2.67,
        "cvr": 4.0,
        "roas_ma7": 3.6
      }
    ]
  },
  "insights": "### 📊 3줄 요약\n1. ...\n2. ...\n3. ..."
}
```

**에러**:
- `400 Bad Request`: 필수 컬럼 누락
  ```json
  {
    "error": "필수 컬럼 누락: ['date', 'spend']"
  }
  ```
- `413 Payload Too Large`: 파일 크기 초과 (10MB)

---

## 4. 수기 데이터 입력

### POST /api/ad-analysis/manual-input

**설명**: 수기로 일별 데이터 입력

**인증**: 필수

**Request Body**:
```json
{
  "snapshot_name": "11월 2주차",
  "data": [
    {
      "date": "2024-11-01",
      "campaign_name": "블프_신규",
      "spend": 150000,
      "impressions": 45000,
      "clicks": 1200,
      "conversions": 48,
      "revenue": 540000
    },
    {
      "date": "2024-11-02",
      "campaign_name": "블프_신규",
      "spend": 140000,
      "impressions": 42000,
      "clicks": 1150,
      "conversions": 45,
      "revenue": 510000
    }
  ]
}
```

**응답**: `200 OK`
```json
{
  "success": true,
  "snapshot_id": 124,
  "metrics": { /* 파일 업로드와 동일 */ }
}
```

---

## 5. 저장된 분석 목록 조회

### GET /api/ad-analysis/snapshots

**설명**: 사용자의 저장된 분석 목록 조회

**인증**: 필수

**Query Parameters**:
| 파라미터 | 타입 | 필수 | 설명 |
|---------|------|------|------|
| saved_only | boolean | No | true: 저장된 것만, false: 전체 (기본값: false) |

**응답**: `200 OK`
```json
{
  "snapshots": [
    {
      "id": 123,
      "snapshot_name": "11월 2주차",
      "period_start": "2024-11-04",
      "period_end": "2024-11-10",
      "created_at": "2024-11-11T10:00:00",
      "updated_at": "2024-11-11T15:30:00",
      "is_saved": true,
      "tags": "블프,신규캠페인",
      "memo": "소재 A 테스트",
      "metrics_summary": {
        "avg_roas": 3.5,
        "total_spend": 5800000,
        "total_revenue": 20300000
      }
    }
  ]
}
```

---

## 6. 분석 상세 조회

### GET /api/ad-analysis/snapshots/:id

**설명**: 특정 분석의 상세 데이터 조회

**인증**: 필수

**Path Parameters**:
| 파라미터 | 타입 | 설명 |
|---------|------|------|
| id | integer | 스냅샷 ID |

**응답**: `200 OK`
```json
{
  "snapshot": {
    "id": 123,
    "user_id": "user123",
    "snapshot_name": "11월 2주차",
    "period_start": "2024-11-04",
    "period_end": "2024-11-10",
    "created_at": "2024-11-11T10:00:00",
    "is_saved": true,
    "tags": "블프,신규캠페인",
    "memo": "소재 A 테스트"
  },
  "metrics": { /* calculate_metrics 결과 */ },
  "insights": "AI 생성 인사이트 텍스트",
  "daily_data": [
    {
      "id": 456,
      "snapshot_id": 123,
      "date": "2024-11-04",
      "campaign_name": "블프_신규",
      "spend": 150000,
      "impressions": 45000,
      "clicks": 1200,
      "conversions": 48,
      "revenue": 540000
    }
  ]
}
```

**에러**:
- `403 Forbidden`: 다른 사용자의 스냅샷
- `404 Not Found`: 존재하지 않는 ID

---

## 7. 분석 저장/수정

### PUT /api/ad-analysis/snapshots/:id

**설명**: 분석 정보 수정 (이름, 태그, 메모, 저장 상태)

**인증**: 필수

**Path Parameters**:
| 파라미터 | 타입 | 설명 |
|---------|------|------|
| id | integer | 스냅샷 ID |

**Request Body**:
```json
{
  "is_saved": true,
  "snapshot_name": "11월 2주차 (수정)",
  "tags": "블프,신규,테스트",
  "memo": "소재 B로 변경 후 성과 개선"
}
```

**응답**: `200 OK`
```json
{
  "success": true,
  "message": "분석이 저장되었습니다."
}
```

**에러**:
- `403 Forbidden`: 권한 없음

---

## 8. 분석 삭제

### DELETE /api/ad-analysis/snapshots/:id

**설명**: 분석 및 관련 일별 데이터 삭제

**인증**: 필수

**Path Parameters**:
| 파라미터 | 타입 | 설명 |
|---------|------|------|
| id | integer | 스냅샷 ID |

**응답**: `200 OK`
```json
{
  "success": true,
  "message": "분석이 삭제되었습니다."
}
```

**에러**:
- `403 Forbidden`: 권한 없음

---

## 9. 기간 비교 분석

### GET /api/ad-analysis/compare

**설명**: 두 분석 기간의 지표 비교

**인증**: 필수

**Query Parameters**:
| 파라미터 | 타입 | 필수 | 설명 |
|---------|------|------|------|
| snapshot_a | integer | Yes | 기준 분석 ID (최근) |
| snapshot_b | integer | Yes | 비교 분석 ID (이전) |

**응답**: `200 OK`
```json
{
  "snapshot_a": {
    "id": 124,
    "snapshot_name": "11월 2주차",
    "period_start": "2024-11-11",
    "period_end": "2024-11-17"
  },
  "snapshot_b": {
    "id": 123,
    "snapshot_name": "11월 1주차",
    "period_start": "2024-11-04",
    "period_end": "2024-11-10"
  },
  "comparison": {
    "avg_roas": {
      "a": 3.8,
      "b": 3.5,
      "change": 8.6,
      "trend": "up"
    },
    "avg_ctr": {
      "a": 2.9,
      "b": 3.2,
      "change": -9.4,
      "trend": "down"
    },
    "avg_cpa": {
      "a": 12000,
      "b": 13800,
      "change": -13.0,
      "trend": "up"
    },
    "cvr": {
      "a": 2.8,
      "b": 2.7,
      "change": 3.7,
      "trend": "up"
    },
    "avg_cpc": {
      "a": 350,
      "b": 376,
      "change": -6.9,
      "trend": "up"
    }
  },
  "summary": "✓ ROAS 8.6% 개선, CPA 13% 감소\n⚠️ CTR 9.4% 하락"
}
```

---

## 10. 월별 목표 조회

### GET /api/ad-analysis/goals

**설명**: 특정 월의 목표 조회

**인증**: 필수

**Query Parameters**:
| 파라미터 | 타입 | 필수 | 설명 |
|---------|------|------|------|
| year_month | string | Yes | YYYY-MM 형식 |

**응답**: `200 OK`
```json
{
  "goal": {
    "id": 10,
    "user_id": "user123",
    "year_month": "2024-11",
    "budget": 10000000,
    "target_roas": 4.0,
    "target_revenue": 40000000
  }
}
```

**응답** (목표 없음):
```json
{
  "goal": null
}
```

---

## 11. 월별 목표 설정

### POST /api/ad-analysis/goals

**설명**: 월별 목표 설정 또는 업데이트

**인증**: 필수

**Request Body**:
```json
{
  "year_month": "2024-11",
  "budget": 10000000,
  "target_roas": 4.0,
  "target_revenue": 40000000
}
```

**응답**: `200 OK`
```json
{
  "success": true,
  "message": "목표가 저장되었습니다."
}
```

---

## 12. 예산 소진율 계산

### GET /api/ad-analysis/budget-pacing

**설명**: 월별 예산 소진 현황 및 페이싱 분석

**인증**: 필수

**Query Parameters**:
| 파라미터 | 타입 | 필수 | 설명 |
|---------|------|------|------|
| year_month | string | Yes | YYYY-MM 형식 |

**응답**: `200 OK`
```json
{
  "budget": 10000000,
  "spent": 5800000,
  "spent_rate": 58.0,
  "progress_rate": 40.0,
  "status": "FAST",
  "projected_end_date": "2024-11-24",
  "suggestion": "일 예산 50,000원 감축 권장",
  "days_passed": 12,
  "days_total": 30
}
```

**상태 값**:
- `ON_TRACK`: 정상 진행 (spent_rate ≈ progress_rate)
- `FAST`: 빠른 소진 (spent_rate > progress_rate * 1.1)
- `SLOW`: 느린 소진 (spent_rate < progress_rate * 0.9)

**에러**:
```json
{
  "error": "월별 예산이 설정되지 않았습니다"
}
```

---

## 13. 캠페인 메모 조회

### GET /api/ad-analysis/memos

**설명**: 특정 캠페인의 메모 목록 조회

**인증**: 필수

**Query Parameters**:
| 파라미터 | 타입 | 필수 | 설명 |
|---------|------|------|------|
| campaign_name | string | Yes | 캠페인명 |

**응답**: `200 OK`
```json
{
  "memos": [
    {
      "id": 5,
      "user_id": "user123",
      "campaign_name": "블프_신규",
      "memo": "소재 #3으로 교체",
      "created_at": "2024-11-10T14:30:00"
    },
    {
      "id": 8,
      "user_id": "user123",
      "campaign_name": "블프_신규",
      "memo": "타겟팅 범위 확대",
      "created_at": "2024-11-12T09:15:00"
    }
  ]
}
```

---

## 14. 캠페인 메모 작성

### POST /api/ad-analysis/memos

**설명**: 캠페인에 메모 추가

**인증**: 필수

**Request Body**:
```json
{
  "campaign_name": "블프_신규",
  "memo": "소재 #5로 재교체, 성과 개선됨"
}
```

**응답**: `200 OK`
```json
{
  "success": true,
  "memo_id": 12,
  "message": "메모가 저장되었습니다."
}
```

---

## 15. PDF 리포트 생성

### GET /api/ad-analysis/export/pdf/:id

**설명**: 분석 결과를 PDF로 다운로드

**인증**: 필수

**Path Parameters**:
| 파라미터 | 타입 | 설명 |
|---------|------|------|
| id | integer | 스냅샷 ID |

**응답**: `200 OK`
- Content-Type: `application/pdf`
- Content-Disposition: `attachment; filename="ad_report_123.pdf"`

**에러**:
- `403 Forbidden`: 권한 없음

---

## 16. Excel 리포트 생성

### GET /api/ad-analysis/export/excel/:id

**설명**: 분석 결과를 Excel로 다운로드

**인증**: 필수

**Path Parameters**:
| 파라미터 | 타입 | 설명 |
|---------|------|------|
| id | integer | 스냅샷 ID |

**응답**: `200 OK`
- Content-Type: `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`
- Content-Disposition: `attachment; filename="ad_report_123.xlsx"`

---

## 17. Excel 템플릿 다운로드

### GET /api/ad-analysis/template/:type

**설명**: 업로드용 Excel 템플릿 다운로드

**인증**: 불필요

**Path Parameters**:
| 파라미터 | 타입 | 설명 |
|---------|------|------|
| type | string | 템플릿 종류: `generic`, `naver`, `meta`, `google`, `kakao` |

**응답**: `200 OK`
- Content-Type: `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`
- Content-Disposition: `attachment; filename="ad_template_{type}.xlsx"`

**예시**:
- `/api/ad-analysis/template/generic` → 범용 템플릿
- `/api/ad-analysis/template/naver` → 네이버 광고 형식

---

## 에러 코드

| 상태 코드 | 설명 | 예시 |
|-----------|------|------|
| 400 | Bad Request | 필수 파라미터 누락, 잘못된 형식 |
| 401 | Unauthorized | 로그인 필요 |
| 403 | Forbidden | 권한 없음 (다른 사용자의 데이터) |
| 404 | Not Found | 존재하지 않는 리소스 |
| 413 | Payload Too Large | 파일 크기 초과 |
| 500 | Internal Server Error | 서버 오류 |

## Rate Limiting

현재 Rate Limiting은 구현되지 않았습니다. 추후 도입 시:
- **일반 API**: 100 requests/minute
- **파일 업로드**: 10 requests/minute
- **AI 인사이트**: 20 requests/hour

## 버전 관리

현재 버전: `v1.0`

API 버전은 URL에 포함되지 않으며, 향후 변경 시 `/api/v2/`와 같이 버전을 명시할 예정입니다.
