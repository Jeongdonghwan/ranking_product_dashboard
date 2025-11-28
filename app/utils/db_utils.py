"""
데이터베이스 유틸리티 함수
- 연결 풀링
- 쿼리 실행
- 트랜잭션 관리
"""

import pymysql
from pymysql.cursors import DictCursor
from contextlib import contextmanager
import logging
from flask import current_app

logger = logging.getLogger(__name__)


class DatabaseError(Exception):
    """데이터베이스 오류 커스텀 예외"""
    pass


def get_db_connection():
    """
    데이터베이스 연결 생성

    Returns:
        pymysql.Connection: 데이터베이스 연결 객체

    Raises:
        DatabaseError: 연결 실패 시
    """
    try:
        connection = pymysql.connect(
            host=current_app.config['DB_HOST'],
            port=current_app.config['DB_PORT'],
            user=current_app.config['DB_USER'],
            password=current_app.config['DB_PASSWORD'],
            database=current_app.config['DB_NAME'],
            charset='utf8mb4',
            cursorclass=DictCursor,
            autocommit=False  # 명시적 트랜잭션 관리
        )
        return connection
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        raise DatabaseError(f"데이터베이스 연결 실패: {str(e)}")


@contextmanager
def get_db_cursor(commit=False):
    """
    Context manager for database cursor
    자동으로 연결 및 커서 정리

    Args:
        commit (bool): True면 자동 커밋, False면 롤백

    Yields:
        pymysql.cursors.DictCursor: 커서 객체

    Example:
        with get_db_cursor(commit=True) as cursor:
            cursor.execute("INSERT INTO table VALUES (%s)", (value,))
    """
    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor()

        yield cursor

        if commit:
            connection.commit()
            logger.debug("Transaction committed")

    except Exception as e:
        if connection:
            connection.rollback()
            logger.error(f"Transaction rolled back: {e}")
        raise DatabaseError(f"쿼리 실행 실패: {str(e)}")

    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()


def execute_query(sql, params=None, fetch_one=False, fetch_all=True):
    """
    SELECT 쿼리 실행 (읽기 전용)

    Args:
        sql (str): SQL 쿼리
        params (tuple): 쿼리 파라미터
        fetch_one (bool): True면 단일 결과 반환
        fetch_all (bool): True면 전체 결과 반환

    Returns:
        dict | list | None: 쿼리 결과

    Example:
        # 단일 결과
        user = execute_query("SELECT * FROM users WHERE id = %s", (user_id,), fetch_one=True)

        # 전체 결과
        users = execute_query("SELECT * FROM users WHERE active = 1")
    """
    with get_db_cursor() as cursor:
        cursor.execute(sql, params or ())

        if fetch_one:
            result = cursor.fetchone()
            logger.debug(f"Query executed (fetch_one): {cursor.rowcount} rows")
            return result

        if fetch_all:
            results = cursor.fetchall()
            logger.debug(f"Query executed (fetch_all): {len(results)} rows")
            return results

        return None


def execute_insert(sql, params=None):
    """
    INSERT 쿼리 실행

    Args:
        sql (str): INSERT SQL 쿼리
        params (tuple): 쿼리 파라미터

    Returns:
        int: 삽입된 행의 ID (AUTO_INCREMENT)

    Example:
        snapshot_id = execute_insert(
            "INSERT INTO ad_analysis_snapshots (user_id, name) VALUES (%s, %s)",
            (user_id, name)
        )
    """
    with get_db_cursor(commit=True) as cursor:
        cursor.execute(sql, params or ())
        inserted_id = cursor.lastrowid
        logger.info(f"Inserted row ID: {inserted_id}")
        return inserted_id


def execute_update(sql, params=None):
    """
    UPDATE 쿼리 실행

    Args:
        sql (str): UPDATE SQL 쿼리
        params (tuple): 쿼리 파라미터

    Returns:
        int: 영향받은 행의 개수

    Example:
        rows_affected = execute_update(
            "UPDATE ad_analysis_snapshots SET is_saved = %s WHERE id = %s",
            (True, snapshot_id)
        )
    """
    with get_db_cursor(commit=True) as cursor:
        cursor.execute(sql, params or ())
        affected_rows = cursor.rowcount
        logger.info(f"Updated {affected_rows} rows")
        return affected_rows


def execute_delete(sql, params=None):
    """
    DELETE 쿼리 실행

    Args:
        sql (str): DELETE SQL 쿼리
        params (tuple): 쿼리 파라미터

    Returns:
        int: 삭제된 행의 개수

    Example:
        rows_deleted = execute_delete(
            "DELETE FROM ad_analysis_snapshots WHERE id = %s",
            (snapshot_id,)
        )
    """
    with get_db_cursor(commit=True) as cursor:
        cursor.execute(sql, params or ())
        deleted_rows = cursor.rowcount
        logger.info(f"Deleted {deleted_rows} rows")
        return deleted_rows


def execute_many(sql, params_list):
    """
    배치 INSERT/UPDATE 실행

    Args:
        sql (str): SQL 쿼리 (동일한 쿼리 반복)
        params_list (list): 파라미터 리스트

    Returns:
        int: 영향받은 총 행의 개수

    Example:
        # 일별 데이터 배치 삽입
        sql = "INSERT INTO ad_daily_data (snapshot_id, date, spend) VALUES (%s, %s, %s)"
        params = [
            (snapshot_id, '2024-11-01', 150000),
            (snapshot_id, '2024-11-02', 160000),
            (snapshot_id, '2024-11-03', 170000)
        ]
        execute_many(sql, params)
    """
    with get_db_cursor(commit=True) as cursor:
        cursor.executemany(sql, params_list)
        affected_rows = cursor.rowcount
        logger.info(f"Batch executed: {affected_rows} rows affected")
        return affected_rows


def check_table_exists(table_name):
    """
    테이블 존재 여부 확인

    Args:
        table_name (str): 테이블명

    Returns:
        bool: 존재 여부
    """
    sql = """
        SELECT COUNT(*) as count
        FROM information_schema.tables
        WHERE table_schema = %s AND table_name = %s
    """
    result = execute_query(
        sql,
        (current_app.config['DB_NAME'], table_name),
        fetch_one=True
    )

    exists = result and result['count'] > 0
    logger.debug(f"Table '{table_name}' exists: {exists}")
    return exists


def get_user_by_id(user_id):
    """
    사용자 정보 조회 (users 테이블)

    Args:
        user_id (str): 사용자 ID

    Returns:
        dict | None: 사용자 정보
    """
    sql = "SELECT * FROM users WHERE user_id = %s"
    return execute_query(sql, (user_id,), fetch_one=True)


def verify_user_exists(user_id):
    """
    사용자 존재 여부 확인

    Args:
        user_id (str): 사용자 ID

    Returns:
        bool: 존재 여부

    Raises:
        DatabaseError: 사용자가 존재하지 않을 경우
    """
    user = get_user_by_id(user_id)
    if not user:
        raise DatabaseError(f"사용자를 찾을 수 없습니다: {user_id}")
    return True


@contextmanager
def transaction():
    """
    명시적 트랜잭션 관리

    Example:
        with transaction() as cursor:
            cursor.execute("INSERT INTO table1 ...")
            cursor.execute("UPDATE table2 ...")
            # 자동 커밋
    """
    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor()

        yield cursor

        connection.commit()
        logger.debug("Transaction committed successfully")

    except Exception as e:
        if connection:
            connection.rollback()
            logger.error(f"Transaction rolled back due to error: {e}")
        raise DatabaseError(f"트랜잭션 실패: {str(e)}")

    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()


def init_database():
    """
    데이터베이스 초기화 및 테이블 존재 여부 확인

    애플리케이션 시작 시 호출

    Returns:
        bool: 초기화 성공 여부
    """
    required_tables = [
        'users',
        'ad_analysis_snapshots',
        'ad_daily_data',
        'ad_campaign_memos',
        'ad_monthly_goals'
    ]

    missing_tables = []

    for table in required_tables:
        if not check_table_exists(table):
            missing_tables.append(table)

    if missing_tables:
        logger.error(f"Missing required tables: {missing_tables}")
        return False

    logger.info("Database initialization successful - all tables exist")
    return True


def get_table_stats():
    """
    테이블 통계 조회 (디버깅/모니터링용)

    Returns:
        list: 테이블별 통계
    """
    sql = """
        SELECT
            table_name AS '테이블',
            ROUND(((data_length + index_length) / 1024 / 1024), 2) AS '크기_MB',
            table_rows AS '행수'
        FROM information_schema.TABLES
        WHERE table_schema = %s
        AND table_name LIKE 'ad_%'
        ORDER BY (data_length + index_length) DESC
    """

    return execute_query(sql, (current_app.config['DB_NAME'],))
