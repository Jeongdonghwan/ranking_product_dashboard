# 데이터베이스 설정 가이드

## 문제 진단 결과

### 핵심 문제
**MariaDB 인증 플러그인 호환성 문제**로 인해 PyMySQL이 데이터베이스에 연결할 수 없습니다.

```
오류: (2059, "Authentication plugin 'auth_gssapi_client' not configured")
```

### 영향 범위
- ❌ 관리자 로그인 불가 (admin_users 테이블 조회 실패)
- ❌ 배너 조회 실패 (banners 테이블 조회 실패)
- ❌ 모든 데이터베이스 작업 실패

### 근본 원인
1. **데이터베이스 테이블이 아직 생성되지 않음**
2. PyMySQL 라이브러리가 MariaDB의 `auth_gssapi_client` 인증 플러그인을 지원하지 않음
3. Python 스크립트로 직접 데이터베이스 연결 시도 → 인증 실패

---

## 해결 방법

### 방법 1: SQL 파일을 직접 실행 (권장)

MariaDB 클라이언트(HeidiSQL, MySQL Workbench, phpMyAdmin 등)를 사용하여 테이블을 생성합니다.

#### 단계:
1. **MariaDB 클라이언트 프로그램 열기**
   - HeidiSQL, MySQL Workbench, phpMyAdmin 등

2. **mbizsquare 데이터베이스에 연결**
   - Host: localhost
   - Port: 3306
   - User: root
   - Database: mbizsquare

3. **SQL 파일 실행**
   ```
   파일 열기: C:\Users\JDH\Downloads\insight\create_banner_tables.sql
   ```

4. **실행 확인**
   - 4개 테이블 생성 확인: banners, admin_users, admin_sessions, banner_analytics
   - 관리자 계정 1개 생성 확인

---

### 방법 2: 명령줄에서 SQL 실행 (MySQL 클라이언트가 설치된 경우)

Windows PowerShell에서:

```powershell
# MySQL 클라이언트 경로 확인 (예시)
& "C:\Program Files\MariaDB 10.x\bin\mysql.exe" -u root -p mbizsquare < C:\Users\JDH\Downloads\insight\create_banner_tables.sql
```

또는:

```cmd
mysql -u root -p mbizsquare < C:\Users\JDH\Downloads\insight\create_banner_tables.sql
```

비밀번호 입력 후 엔터 → 테이블 자동 생성

---

## 생성되는 테이블

### 1. banners
배너 데이터 저장
- banner_type: 배너 타입 (home_top, home_bottom, home_grid, grid_general, grid_coupang)
- title: 배너 제목
- image_url: 이미지 경로
- link_url: 클릭 시 이동할 URL
- is_active: 활성화 여부
- position_order: 정렬 순서
- click_count, impression_count: 클릭/노출 수

### 2. admin_users
관리자 계정
- username: 관리자 아이디
- password_hash: bcrypt 암호화된 비밀번호

### 3. admin_sessions
관리자 세션 (로그인 토큰)
- admin_id: 관리자 ID (외래키)
- session_token: 세션 토큰 (64자)
- expires_at: 만료 시간 (8시간)

### 4. banner_analytics
배너 통계 데이터
- banner_id: 배너 ID (외래키)
- event_type: 이벤트 타입 (impression/click)
- event_date: 날짜
- event_count: 카운트

---

## 초기 관리자 계정

테이블 생성 후 자동으로 생성되는 관리자 계정:

```
아이디: admin
비밀번호: admin2024!@
```

---

## 테이블 생성 후 테스트

### 1. 관리자 로그인 테스트

브라우저에서:
```
http://127.0.0.1:8080/admin/login
```

아이디: `admin`
비밀번호: `admin2024!@`

로그인 성공 시 → 배너 관리 페이지로 리다이렉트

### 2. 배너 API 테스트

```python
python test_banner_system.py
```

예상 결과:
- ✅ 관리자 로그인 성공
- ✅ 배너 조회 API 정상 작동
- ✅ 모든 테스트 통과

---

## 문제 해결 확인사항

### 테이블이 정상적으로 생성되었는지 확인

MariaDB 클라이언트에서:

```sql
USE mbizsquare;

SHOW TABLES LIKE '%banner%';
SHOW TABLES LIKE '%admin%';

-- 테이블 구조 확인
DESCRIBE banners;
DESCRIBE admin_users;
DESCRIBE admin_sessions;
DESCRIBE banner_analytics;

-- 관리자 계정 확인
SELECT * FROM admin_users;
```

예상 출력:
- banners 테이블 존재
- admin_users 테이블 존재 (1개 레코드: username='admin')
- admin_sessions 테이블 존재
- banner_analytics 테이블 존재

---

## 추가 지원이 필요한 경우

### MariaDB 클라이언트가 없는 경우

#### HeidiSQL 다운로드 (무료, Windows)
https://www.heidisql.com/download.php

#### MySQL Workbench 다운로드 (무료, 크로스 플랫폼)
https://dev.mysql.com/downloads/workbench/

### 여전히 연결 오류가 발생하는 경우

MariaDB 사용자 인증 플러그인 변경:

```sql
-- MariaDB 클라이언트에서 실행
ALTER USER 'root'@'localhost' IDENTIFIED VIA mysql_native_password USING PASSWORD('');
FLUSH PRIVILEGES;
```

---

## 요약

1. **SQL 파일 실행**: `create_banner_tables.sql` 파일을 MariaDB 클라이언트로 실행
2. **테이블 생성 확인**: 4개 테이블 + 관리자 계정 1개 확인
3. **로그인 테스트**: http://127.0.0.1:8080/admin/login
4. **테스트 스크립트 실행**: `python test_banner_system.py`

완료!
