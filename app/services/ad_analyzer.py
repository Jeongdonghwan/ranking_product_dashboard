"""
광고 분석 서비스
- 데이터 저장 및 조회
- 지표 계산 (ROAS, CTR, CPA, CVR 등)
- 캠페인 통계
- 기간 비교
- 예산 페이싱
"""

import pandas as pd
import numpy as np
import json
import logging
from datetime import datetime, timedelta
from calendar import monthrange

from app.utils.db_utils import (
    execute_query, execute_insert, execute_update,
    execute_delete, execute_many, transaction
)
from app.utils.helpers import (
    calculate_roas, calculate_ctr, calculate_cpc,
    calculate_cpa, calculate_cvr, sanitize_campaign_name
)

logger = logging.getLogger(__name__)


class AdAnalyzer:
    """광고 데이터 분석 서비스 클래스"""

    def __init__(self, user_id):
        """
        Args:
            user_id (str): 사용자 ID
        """
        self.user_id = user_id

    def save_snapshot(self, df, snapshot_name):
        """
        데이터프레임을 스냅샷으로 저장

        Args:
            df (pandas.DataFrame): 광고 데이터
            snapshot_name (str): 스냅샷 이름

        Returns:
            int: 생성된 snapshot_id

        Required DataFrame columns:
            - date: 날짜 (YYYY-MM-DD)
            - campaign_name: 캠페인명
            - spend: 지출액
            - clicks: 클릭수
            - conversions: 전환수
            - revenue: 매출액
            - impressions: 노출수 (선택)
        """
        try:
            # 캠페인명 정제
            df['campaign_name'] = df['campaign_name'].apply(sanitize_campaign_name)

            # 날짜 변환
            df['date'] = pd.to_datetime(df['date']).dt.date

            # 기간 추출
            period_start = df['date'].min()
            period_end = df['date'].max()

            # 데이터 JSON 변환
            data_json = df.to_json(orient='records', date_format='iso')

            # 스냅샷 생성
            with transaction() as cursor:
                # 스냅샷 테이블에 삽입
                snapshot_sql = """
                    INSERT INTO ad_analysis_snapshots
                    (user_id, snapshot_name, period_start, period_end, data_json)
                    VALUES (%s, %s, %s, %s, %s)
                """
                cursor.execute(snapshot_sql, (
                    self.user_id,
                    snapshot_name,
                    period_start,
                    period_end,
                    data_json
                ))

                snapshot_id = cursor.lastrowid
                logger.info(f"Created snapshot {snapshot_id} for user {self.user_id}")

                # 일별 데이터 삽입
                daily_data_sql = """
                    INSERT INTO ad_daily_data
                    (snapshot_id, date, campaign_name, spend, impressions, clicks, conversions, revenue)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """

                daily_records = []
                for _, row in df.iterrows():
                    daily_records.append((
                        snapshot_id,
                        row['date'],
                        row['campaign_name'],
                        float(row['spend']),
                        int(row.get('impressions', 0)),
                        int(row['clicks']),
                        int(row['conversions']),
                        float(row['revenue'])
                    ))

                cursor.executemany(daily_data_sql, daily_records)
                logger.info(f"Inserted {len(daily_records)} daily records for snapshot {snapshot_id}")

            return snapshot_id

        except Exception as e:
            logger.error(f"Failed to save snapshot: {e}")
            raise

    def calculate_metrics(self, snapshot_id):
        """
        스냅샷의 모든 지표 계산

        Args:
            snapshot_id (int): 스냅샷 ID

        Returns:
            dict: 계산된 지표
        """
        try:
            # 일별 데이터 조회
            sql = """
                SELECT * FROM ad_daily_data
                WHERE snapshot_id = %s
                ORDER BY date
            """
            data = execute_query(sql, (snapshot_id,))

            if not data:
                logger.warning(f"No data found for snapshot {snapshot_id}")
                return {}

            df = pd.DataFrame(data)

            # 전체 지표 계산
            total_spend = df['spend'].sum()
            total_revenue = df['revenue'].sum()
            total_clicks = df['clicks'].sum()
            total_conversions = df['conversions'].sum()
            total_impressions = df['impressions'].sum()

            metrics = {
                # 기본 지표
                'total_spend': float(total_spend),
                'total_revenue': float(total_revenue),
                'total_clicks': int(total_clicks),
                'total_conversions': int(total_conversions),
                'total_impressions': int(total_impressions),

                # 계산 지표
                'avg_roas': calculate_roas(total_revenue, total_spend),
                'avg_ctr': calculate_ctr(total_clicks, total_impressions),
                'avg_cpc': calculate_cpc(total_spend, total_clicks),
                'avg_cpa': calculate_cpa(total_spend, total_conversions),
                'cvr': calculate_cvr(total_conversions, total_clicks),
                'avg_order_value': round(total_revenue / total_conversions, 0) if total_conversions > 0 else 0,

                # 캠페인별 통계
                'campaigns': self._calculate_campaign_metrics(df),

                # 일별 트렌드
                'daily_trend': self._calculate_daily_trend(df),

                # 기간 정보
                'period_start': str(df['date'].min()),
                'period_end': str(df['date'].max()),
                'total_days': len(df['date'].unique())
            }

            # metrics_summary 업데이트
            update_sql = """
                UPDATE ad_analysis_snapshots
                SET metrics_summary = %s
                WHERE id = %s
            """
            execute_update(update_sql, (json.dumps(metrics), snapshot_id))

            logger.info(f"Metrics calculated for snapshot {snapshot_id}")

            return metrics

        except Exception as e:
            logger.error(f"Failed to calculate metrics: {e}")
            raise

    def _calculate_campaign_metrics(self, df):
        """캠페인별 지표 계산"""
        campaign_stats = df.groupby('campaign_name').agg({
            'spend': 'sum',
            'revenue': 'sum',
            'clicks': 'sum',
            'conversions': 'sum',
            'impressions': 'sum'
        }).reset_index()

        # 계산 지표 추가
        campaign_stats['roas'] = campaign_stats.apply(
            lambda row: calculate_roas(row['revenue'], row['spend']), axis=1
        )
        campaign_stats['ctr'] = campaign_stats.apply(
            lambda row: calculate_ctr(row['clicks'], row['impressions']), axis=1
        )
        campaign_stats['cpa'] = campaign_stats.apply(
            lambda row: calculate_cpa(row['spend'], row['conversions']), axis=1
        )
        campaign_stats['cvr'] = campaign_stats.apply(
            lambda row: calculate_cvr(row['conversions'], row['clicks']), axis=1
        )
        campaign_stats['cpc'] = campaign_stats.apply(
            lambda row: calculate_cpc(row['spend'], row['clicks']), axis=1
        )

        # ROAS 순위 계산
        campaign_stats = campaign_stats.sort_values('roas', ascending=False)
        campaign_stats['rank'] = range(1, len(campaign_stats) + 1)

        # 상태 판정 (ROAS 기준)
        def get_status(roas):
            if roas >= 4.0:
                return 'excellent'
            elif roas >= 3.0:
                return 'good'
            else:
                return 'poor'

        campaign_stats['status'] = campaign_stats['roas'].apply(get_status)

        # 숫자 타입 변환
        for col in ['spend', 'revenue']:
            campaign_stats[col] = campaign_stats[col].astype(float)

        for col in ['clicks', 'conversions', 'impressions']:
            campaign_stats[col] = campaign_stats[col].astype(int)

        return campaign_stats.to_dict('records')

    def _calculate_daily_trend(self, df):
        """일별 트렌드 계산"""
        daily = df.groupby('date').agg({
            'spend': 'sum',
            'revenue': 'sum',
            'clicks': 'sum',
            'conversions': 'sum',
            'impressions': 'sum'
        }).reset_index()

        # 계산 지표 추가
        daily['roas'] = daily.apply(
            lambda row: calculate_roas(row['revenue'], row['spend']), axis=1
        )
        daily['ctr'] = daily.apply(
            lambda row: calculate_ctr(row['clicks'], row['impressions']), axis=1
        )
        daily['cvr'] = daily.apply(
            lambda row: calculate_cvr(row['conversions'], row['clicks']), axis=1
        )

        # 7일 이동평균 계산
        daily['roas_ma7'] = daily['roas'].rolling(window=7, min_periods=1).mean().round(2)

        # 날짜를 문자열로 변환
        daily['date'] = daily['date'].astype(str)

        # 숫자 타입 변환
        for col in ['spend', 'revenue']:
            daily[col] = daily[col].astype(float)

        for col in ['clicks', 'conversions', 'impressions']:
            daily[col] = daily[col].astype(int)

        return daily.to_dict('records')

    def get_snapshots(self, saved_only=False):
        """
        저장된 분석 목록 조회

        Args:
            saved_only (bool): True면 저장된 것만

        Returns:
            list: 스냅샷 목록
        """
        sql = """
            SELECT
                id,
                snapshot_name,
                period_start,
                period_end,
                metrics_summary,
                created_at,
                tags,
                memo,
                is_saved
            FROM ad_analysis_snapshots
            WHERE user_id = %s
        """

        if saved_only:
            sql += " AND is_saved = TRUE"

        sql += " ORDER BY created_at DESC"

        snapshots = execute_query(sql, (self.user_id,))

        # metrics_summary JSON 파싱
        for snapshot in snapshots:
            if snapshot['metrics_summary']:
                try:
                    snapshot['metrics_summary'] = json.loads(snapshot['metrics_summary'])
                except:
                    snapshot['metrics_summary'] = {}

            # 날짜 포맷팅
            snapshot['period_start'] = str(snapshot['period_start'])
            snapshot['period_end'] = str(snapshot['period_end'])
            snapshot['created_at'] = snapshot['created_at'].strftime('%Y-%m-%d %H:%M:%S')

        return snapshots

    def get_snapshot_detail(self, snapshot_id):
        """
        특정 스냅샷의 상세 정보 조회

        Args:
            snapshot_id (int): 스냅샷 ID

        Returns:
            dict: 상세 정보
        """
        # 스냅샷 정보
        snapshot_sql = """
            SELECT * FROM ad_analysis_snapshots
            WHERE id = %s AND user_id = %s
        """
        snapshot = execute_query(snapshot_sql, (snapshot_id, self.user_id), fetch_one=True)

        if not snapshot:
            raise ValueError(f"Snapshot not found: {snapshot_id}")

        # 일별 데이터
        daily_sql = """
            SELECT * FROM ad_daily_data
            WHERE snapshot_id = %s
            ORDER BY date
        """
        daily_data = execute_query(daily_sql, (snapshot_id,))

        # metrics_summary 파싱
        metrics = {}
        if snapshot['metrics_summary']:
            try:
                metrics = json.loads(snapshot['metrics_summary'])
            except:
                pass

        # AI 인사이트
        insights = snapshot.get('ai_insights', '')

        # 날짜 포맷팅
        snapshot['period_start'] = str(snapshot['period_start'])
        snapshot['period_end'] = str(snapshot['period_end'])

        for record in daily_data:
            record['date'] = str(record['date'])
            record['spend'] = float(record['spend'])
            record['revenue'] = float(record['revenue'])

        return {
            'snapshot': snapshot,
            'daily_data': daily_data,
            'metrics': metrics,
            'insights': insights,
            'campaigns': metrics.get('campaigns', [])
        }

    def update_snapshot(self, snapshot_id, updates):
        """
        스냅샷 업데이트 (저장, 태그, 메모)

        Args:
            snapshot_id (int): 스냅샷 ID
            updates (dict): 업데이트할 필드

        Returns:
            bool: 성공 여부
        """
        allowed_fields = ['is_saved', 'snapshot_name', 'tags', 'memo']
        update_fields = []
        params = []

        for field in allowed_fields:
            if field in updates:
                update_fields.append(f"{field} = %s")
                params.append(updates[field])

        if not update_fields:
            return True

        sql = f"""
            UPDATE ad_analysis_snapshots
            SET {', '.join(update_fields)}
            WHERE id = %s AND user_id = %s
        """

        params.extend([snapshot_id, self.user_id])

        rows_affected = execute_update(sql, tuple(params))

        logger.info(f"Updated snapshot {snapshot_id}: {rows_affected} rows")

        return rows_affected > 0

    def delete_snapshot(self, snapshot_id):
        """
        스냅샷 삭제 (CASCADE로 일별 데이터도 자동 삭제)

        Args:
            snapshot_id (int): 스냅샷 ID

        Returns:
            bool: 성공 여부
        """
        sql = """
            DELETE FROM ad_analysis_snapshots
            WHERE id = %s AND user_id = %s
        """

        rows_deleted = execute_delete(sql, (snapshot_id, self.user_id))

        logger.info(f"Deleted snapshot {snapshot_id}: {rows_deleted} rows")

        return rows_deleted > 0

    def check_ownership(self, snapshot_id):
        """
        스냅샷 소유권 확인

        Args:
            snapshot_id (int): 스냅샷 ID

        Returns:
            bool: 소유권 여부
        """
        sql = """
            SELECT user_id FROM ad_analysis_snapshots
            WHERE id = %s
        """
        result = execute_query(sql, (snapshot_id,), fetch_one=True)

        return result and result['user_id'] == self.user_id

    def save_insights(self, snapshot_id, insights):
        """
        AI 인사이트 저장

        Args:
            snapshot_id (int): 스냅샷 ID
            insights (str): AI 생성 인사이트

        Returns:
            bool: 성공 여부
        """
        sql = """
            UPDATE ad_analysis_snapshots
            SET ai_insights = %s
            WHERE id = %s AND user_id = %s
        """

        rows_affected = execute_update(sql, (insights, snapshot_id, self.user_id))

        return rows_affected > 0

    def compare_snapshots(self, snapshot_a_id, snapshot_b_id):
        """
        두 스냅샷 비교 분석

        Args:
            snapshot_a_id (int): 기준 스냅샷 ID (현재)
            snapshot_b_id (int): 비교 스냅샷 ID (이전)

        Returns:
            dict: 비교 결과
        """
        # 두 스냅샷의 지표 조회
        metrics_a = self._get_snapshot_metrics(snapshot_a_id)
        metrics_b = self._get_snapshot_metrics(snapshot_b_id)

        comparison = {}

        metrics_to_compare = ['avg_roas', 'avg_ctr', 'avg_cpa', 'cvr', 'avg_cpc']

        for key in metrics_to_compare:
            val_a = metrics_a.get(key, 0)
            val_b = metrics_b.get(key, 0)

            if val_b > 0:
                change_pct = round(((val_a - val_b) / val_b * 100), 1)
            else:
                change_pct = 0.0

            # CPA, CPC는 낮을수록 좋음
            if key in ['avg_cpa', 'avg_cpc']:
                trend = 'up' if change_pct < 0 else ('down' if change_pct > 0 else 'flat')
            else:
                trend = 'up' if change_pct > 0 else ('down' if change_pct < 0 else 'flat')

            comparison[key] = {
                'a': val_a,
                'b': val_b,
                'change': change_pct,
                'trend': trend
            }

        # 개선 요약 생성
        summary = self._generate_comparison_summary(comparison)

        return {
            'comparison': comparison,
            'summary': summary,
            'snapshot_a': self._get_snapshot_info(snapshot_a_id),
            'snapshot_b': self._get_snapshot_info(snapshot_b_id)
        }

    def _get_snapshot_metrics(self, snapshot_id):
        """스냅샷의 metrics_summary 조회"""
        sql = "SELECT metrics_summary FROM ad_analysis_snapshots WHERE id = %s"
        result = execute_query(sql, (snapshot_id,), fetch_one=True)

        if result and result['metrics_summary']:
            try:
                return json.loads(result['metrics_summary'])
            except:
                pass

        return {}

    def _get_snapshot_info(self, snapshot_id):
        """스냅샷 기본 정보 조회"""
        sql = """
            SELECT id, snapshot_name, period_start, period_end
            FROM ad_analysis_snapshots
            WHERE id = %s
        """
        snapshot = execute_query(sql, (snapshot_id,), fetch_one=True)

        if snapshot:
            snapshot['period_start'] = str(snapshot['period_start'])
            snapshot['period_end'] = str(snapshot['period_end'])

        return snapshot

    def _generate_comparison_summary(self, comparison):
        """비교 요약 텍스트 생성"""
        improvements = []
        declines = []

        labels = {
            'avg_roas': 'ROAS',
            'avg_ctr': 'CTR',
            'avg_cpa': 'CPA',
            'cvr': '전환율',
            'avg_cpc': 'CPC'
        }

        for key, data in comparison.items():
            change = abs(data['change'])
            if change >= 5:  # 5% 이상 변화만
                label = labels[key]
                if data['trend'] == 'up':
                    if key not in ['avg_cpa', 'avg_cpc']:
                        improvements.append(f"{label} {change}% 개선")
                    else:
                        declines.append(f"{label} {change}% 증가")
                elif data['trend'] == 'down':
                    if key not in ['avg_cpa', 'avg_cpc']:
                        declines.append(f"{label} {change}% 하락")
                    else:
                        improvements.append(f"{label} {change}% 감소")

        summary = []
        if improvements:
            summary.append("✓ " + ", ".join(improvements))
        if declines:
            summary.append("⚠️ " + ", ".join(declines))

        return "\n".join(summary) if summary else "큰 변화 없음"

    def calculate_budget_pacing(self, year_month):
        """
        예산 소진율 계산

        Args:
            year_month (str): YYYY-MM

        Returns:
            dict: 예산 페이싱 정보
        """
        # 월별 목표 조회
        goal = self._get_monthly_goal(year_month)

        if not goal or not goal.get('budget'):
            return {'error': '월별 예산이 설정되지 않았습니다'}

        budget = float(goal['budget'])

        # 해당 월의 지출 합계
        sql = """
            SELECT COALESCE(SUM(spend), 0) as total_spend
            FROM ad_daily_data d
            JOIN ad_analysis_snapshots s ON d.snapshot_id = s.id
            WHERE s.user_id = %s
            AND DATE_FORMAT(d.date, '%%Y-%%m') = %s
        """
        result = execute_query(sql, (self.user_id, year_month), fetch_one=True)
        spent = float(result['total_spend'] or 0)

        # 진행률 계산
        year, month = map(int, year_month.split('-'))
        today = datetime.now()

        if today.year == year and today.month == month:
            days_in_month = monthrange(year, month)[1]
            days_passed = today.day
        else:
            # 과거 월
            days_in_month = monthrange(year, month)[1]
            days_passed = days_in_month

        progress_rate = round((days_passed / days_in_month * 100), 1)
        spent_rate = round((spent / budget * 100), 1)

        # 페이싱 판정
        if spent_rate > progress_rate * 1.1:
            status = 'FAST'
            daily_avg = spent / days_passed if days_passed > 0 else 0
            projected_days = int(budget / daily_avg) if daily_avg > 0 else days_in_month
            projected_end_date = f"{year_month}-{min(projected_days, days_in_month):02d}"

            remaining_days = days_in_month - days_passed
            remaining_budget = budget - spent
            suggested_daily = int(remaining_budget / remaining_days) if remaining_days > 0 else 0
            current_daily = int(daily_avg)
            adjustment = current_daily - suggested_daily

            suggestion = f"일 예산 {adjustment:,}원 감축 권장"

        elif spent_rate < progress_rate * 0.9:
            status = 'SLOW'
            projected_end_date = f"{year_month}-{days_in_month:02d}"

            remaining_days = days_in_month - days_passed
            remaining_budget = budget - spent
            suggested_daily = int(remaining_budget / remaining_days) if remaining_days > 0 else 0
            daily_avg = spent / days_passed if days_passed > 0 else 0
            adjustment = suggested_daily - int(daily_avg)

            suggestion = f"일 예산 {adjustment:,}원 증액 권장"

        else:
            status = 'ON_TRACK'
            projected_end_date = f"{year_month}-{days_in_month:02d}"
            suggestion = "정상 진행 중"

        return {
            'budget': budget,
            'spent': spent,
            'spent_rate': spent_rate,
            'progress_rate': progress_rate,
            'status': status,
            'projected_end_date': projected_end_date,
            'suggestion': suggestion,
            'days_passed': days_passed,
            'days_total': days_in_month
        }

    def _get_monthly_goal(self, year_month):
        """월별 목표 조회"""
        sql = """
            SELECT * FROM ad_monthly_goals
            WHERE user_id = %s AND year_month = %s
        """
        return execute_query(sql, (self.user_id, year_month), fetch_one=True)
