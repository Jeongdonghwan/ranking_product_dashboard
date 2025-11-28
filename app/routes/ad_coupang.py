"""
쿠팡 광고 분석 전용 라우트
- 쿠팡 대시보드
- 쿠팡 파일 업로드
- 쿠팡 키워드 추천
"""

import os
import pandas as pd
import numpy as np
import logging
from flask import (
    Blueprint, render_template, request, jsonify,
    session, current_app
)

logger = logging.getLogger(__name__)

# Blueprint 생성
coupang_bp = Blueprint('ad_coupang', __name__)


# ========================================
# 쿠팡 대시보드
# ========================================

@coupang_bp.route('/ad-dashboard/coupang-test')
def coupang_manual_test():
    """
    쿠팡 광고 수동 테스트 페이지

    Returns:
        HTML: 수동 테스트 템플릿
    """
    return render_template('manual_test.html')


@coupang_bp.route('/ad-dashboard/coupang')
@coupang_bp.route('/ad-dashboard-coupang')  # 별칭 라우트
# @require_auth  # 테스트를 위해 인증 비활성화
def coupang_dashboard():
    """
    쿠팡 광고 전용 대시보드

    Returns:
        HTML: 쿠팡 대시보드 템플릿
    """
    # 테스트용 임시 사용자 정보
    user = {
        'user_id': 'test_user',
        'username': '테스트 사용자',
        'email': 'test@example.com'
    }

    return render_template('ad_dashboard_coupang.html', user=user)


# ========================================
# 쿠팡 파일 업로드
# ========================================

@coupang_bp.route('/api/ad-analysis/upload-coupang', methods=['POST'])
# @require_auth  # 테스트를 위해 인증 비활성화
def upload_coupang():
    """
    쿠팡 광고 Excel 파일 업로드 및 파싱

    쿠팡 광고 보고서 필수 컬럼:
    - 키워드, 노출수, 클릭수, 광고비, 클릭률
    - 총 주문수(1일), 총 판매수량(1일), 총 전환매출액(1일)
    - 총광고수익률(1일) = ROAS
    """
    user_id = 'test_user'

    if 'file' not in request.files:
        return jsonify({'success': False, 'error': '파일이 없습니다'}), 400

    file = request.files['file']

    if file.filename == '':
        return jsonify({'success': False, 'error': '파일명이 비어있습니다'}), 400

    try:
        # Excel 파일 읽기 (인코딩 문제 해결 - BytesIO 사용)
        import io
        file_content = file.read()
        df = pd.read_excel(io.BytesIO(file_content), engine='openpyxl')
        logger.info(f'Coupang file uploaded: {file.filename}, rows: {len(df)}, columns: {len(df.columns)}')

        # 필수 컬럼 확인 (매출액은 14일 우선, 없으면 1일 사용)
        required_cols_base = ['키워드', '노출수', '클릭수', '광고비', '클릭률']

        # 매출액 컬럼 선택: 14일 우선, 없으면 1일 사용
        if '총 전환매출액(14일)' in df.columns:
            revenue_col = '총 전환매출액(14일)'
            logger.info('Using 14-day revenue data')
        elif '총 전환매출액(1일)' in df.columns:
            revenue_col = '총 전환매출액(1일)'
            logger.info('Using 1-day revenue data (14-day not available)')
        else:
            logger.error('No revenue column found')
            return jsonify({'success': False, 'error': '매출액 컬럼 없음 (총 전환매출액(14일) 또는 총 전환매출액(1일) 필요)'}), 400

        # ROAS 컬럼 선택
        if '총광고수익률(14일)' in df.columns:
            roas_col = '총광고수익률(14일)'
        elif '총광고수익률(1일)' in df.columns:
            roas_col = '총광고수익률(1일)'
        else:
            roas_col = None

        # 주문수/판매수량 컬럼 선택
        if '총 주문수(14일)' in df.columns:
            order_col = '총 주문수(14일)'
            quantity_col = '총 판매수량(14일)' if '총 판매수량(14일)' in df.columns else '총 판매수량(1일)'
        else:
            order_col = '총 주문수(1일)'
            quantity_col = '총 판매수량(1일)'

        required_cols = required_cols_base + [order_col, quantity_col, revenue_col]
        if roas_col:
            required_cols.append(roas_col)

        missing = [col for col in required_cols if col not in df.columns]
        if missing:
            logger.error(f'Missing required columns: {missing}')
            return jsonify({'success': False, 'error': f'필수 컬럼 누락: {missing}'}), 400

        # 컬럼명 통일 (14일/1일 상관없이 동일한 이름으로 사용)
        df = df.rename(columns={
            revenue_col: '총 전환매출액',
            order_col: '총 주문수',
            quantity_col: '총 판매수량'
        })
        if roas_col:
            df = df.rename(columns={roas_col: '총광고수익률'})

        logger.info(f'Column mapping: revenue={revenue_col}, orders={order_col}')

        # 데이터 정제
        # 1. 모든 광고 노출 지면 데이터 포함 (검색영역 + 비검색영역 + 리타겟팅)
        # 키워드가 '-'여도 포함 (비검색영역, 리타겟팅의 키워드는 '-'임)
        if '광고 노출 지면' in df.columns:
            exposure_types = df['광고 노출 지면'].value_counts()
            logger.info(f'Ad exposure types included: {exposure_types.to_dict()}')

        # 🔥 비검색영역 및 리타겟팅 통합 처리
        if '광고 노출 지면' in df.columns:
            # 1) 비검색영역 통합
            non_search_mask = df['광고 노출 지면'].str.contains('비검색', na=False)
            # 2) 리타겟팅 통합
            retargeting_mask = df['광고 노출 지면'].str.contains('리타겟팅', na=False)

            # 검색영역만 남김 (비검색, 리타겟팅 제외)
            search_only_df = df[~(non_search_mask | retargeting_mask)].copy()

            aggregated_rows = []

            # === 비검색영역 통합 ===
            if non_search_mask.sum() > 0:
                non_search_df = df[non_search_mask].copy()
                logger.info(f'비검색영역 통합 전: {non_search_mask.sum()}개 행')

                # 비검색영역 지표 합산
                non_search_aggregated = {
                    '키워드': '비검색영역 (통합)',
                    '광고 노출 지면': '비검색영역 (통합)',
                    '노출수': non_search_df['노출수'].sum(),
                    '클릭수': non_search_df['클릭수'].sum(),
                    '광고비': non_search_df['광고비'].sum(),
                    '총 주문수': non_search_df['총 주문수'].sum(),
                    '총 판매수량': non_search_df['총 판매수량'].sum(),
                    '총 전환매출액': non_search_df['총 전환매출액'].sum()
                }

                # 클릭률 재계산
                if non_search_aggregated['노출수'] > 0:
                    non_search_aggregated['클릭률'] = (non_search_aggregated['클릭수'] / non_search_aggregated['노출수']) * 100
                else:
                    non_search_aggregated['클릭률'] = 0

                # ROAS 재계산 (문자열 형식으로 저장하여 Excel 데이터와 일치)
                if non_search_aggregated['광고비'] > 0:
                    roas_value = (non_search_aggregated['총 전환매출액'] / non_search_aggregated['광고비']) * 100
                    non_search_aggregated['총광고수익률'] = f"{roas_value:.2f}%"
                else:
                    non_search_aggregated['총광고수익률'] = "0.00%"

                aggregated_rows.append(non_search_aggregated)
                logger.info(f'비검색영역 통합 완료: 1개 행으로 통합됨')
            else:
                logger.info('비검색영역 데이터 없음')

            # === 리타겟팅 통합 ===
            if retargeting_mask.sum() > 0:
                retargeting_df = df[retargeting_mask].copy()
                logger.info(f'리타겟팅 통합 전: {retargeting_mask.sum()}개 행')

                # 리타겟팅 지표 합산
                retargeting_aggregated = {
                    '키워드': '리타겟팅 (통합)',
                    '광고 노출 지면': '리타겟팅 (통합)',
                    '노출수': retargeting_df['노출수'].sum(),
                    '클릭수': retargeting_df['클릭수'].sum(),
                    '광고비': retargeting_df['광고비'].sum(),
                    '총 주문수': retargeting_df['총 주문수'].sum(),
                    '총 판매수량': retargeting_df['총 판매수량'].sum(),
                    '총 전환매출액': retargeting_df['총 전환매출액'].sum()
                }

                # 클릭률 재계산
                if retargeting_aggregated['노출수'] > 0:
                    retargeting_aggregated['클릭률'] = (retargeting_aggregated['클릭수'] / retargeting_aggregated['노출수']) * 100
                else:
                    retargeting_aggregated['클릭률'] = 0

                # ROAS 재계산 (문자열 형식으로 저장하여 Excel 데이터와 일치)
                if retargeting_aggregated['광고비'] > 0:
                    roas_value = (retargeting_aggregated['총 전환매출액'] / retargeting_aggregated['광고비']) * 100
                    retargeting_aggregated['총광고수익률'] = f"{roas_value:.2f}%"
                else:
                    retargeting_aggregated['총광고수익률'] = "0.00%"

                aggregated_rows.append(retargeting_aggregated)
                logger.info(f'리타겟팅 통합 완료: 1개 행으로 통합됨')
            else:
                logger.info('리타겟팅 데이터 없음')

            # 통합된 데이터 병합
            if aggregated_rows:
                aggregated_df = pd.DataFrame(aggregated_rows)
                df = pd.concat([search_only_df, aggregated_df], ignore_index=True)
            else:
                df = search_only_df

        logger.info(f'Total keywords to analyze (before dedup): {len(df)}개')

        # 🔥 키워드 중복 제거 - 동일 키워드는 데이터 합산
        if '키워드' in df.columns:
            keyword_groups = df.groupby('키워드', as_index=False).agg({
                '노출수': 'sum',
                '클릭수': 'sum',
                '광고비': 'sum',
                '총 주문수': 'sum',
                '총 판매수량': 'sum',
                '총 전환매출액': 'sum',
                '광고 노출 지면': 'first',  # 첫 번째 값 사용
            })

            # 클릭률 재계산 (Infinity 방지: 노출수가 0인 경우)
            keyword_groups['클릭률'] = (keyword_groups['클릭수'] / keyword_groups['노출수'] * 100).replace([np.inf, -np.inf], 0).fillna(0)

            # ROAS 재계산
            keyword_groups['총광고수익률'] = keyword_groups.apply(
                lambda row: f"{(row['총 전환매출액'] / row['광고비'] * 100):.2f}%" if row['광고비'] > 0 else "0.00%",
                axis=1
            )

            df = keyword_groups
            logger.info(f'Keyword deduplication completed: {len(df)}개 (unique keywords)')

        # 2. 클릭률 처리 (이미 % 형식이면 그대로, 소수점이면 100 곱하기)
        if df['클릭률'].max() <= 1:
            df['클릭률'] = df['클릭률'] * 100

        # 3. ROAS 파싱
        if df['총광고수익률'].dtype == 'object':
            # "356.78%" → 356.78 변환
            df['ROAS'] = df['총광고수익률'].str.rstrip('%').astype(float)
        else:
            df['ROAS'] = df['총광고수익률']
            if df['ROAS'].max() <= 10:  # 소수점 형식 (3.56 → 356)
                df['ROAS'] = df['ROAS'] * 100

        # 4. CPC 계산 (클릭당 단가) - Infinity 방지: 클릭수가 0인 경우
        df['CPC'] = (df['광고비'] / df['클릭수']).replace([np.inf, -np.inf], 0).fillna(0)

        # 5. 결측치 및 Infinity 처리 (JSON 직렬화 오류 방지)
        # 모든 숫자 컬럼에서 Infinity와 NaN을 0으로 변환
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        for col in numeric_cols:
            df[col] = df[col].replace([np.inf, -np.inf], 0).fillna(0)

        logger.info(f'Processed {len(df)} valid keywords')

        # 요약 지표 계산
        total_spend = df['광고비'].sum()
        total_revenue = df['총 전환매출액'].sum()

        # 평균CTR 계산 (Infinity 방지)
        avg_ctr = df['클릭률'].mean()
        if np.isinf(avg_ctr) or np.isnan(avg_ctr):
            avg_ctr = 0

        summary = {
            '총광고비': int(total_spend),
            '총매출액': int(total_revenue),
            '평균ROAS': round((total_revenue / total_spend * 100), 2) if total_spend > 0 else 0,
            '총클릭수': int(df['클릭수'].sum()),
            '평균CTR': round(float(avg_ctr), 2),
            '총노출수': int(df['노출수'].sum()),
            '총주문수': int(df['총 주문수'].sum())
        }

        # JSON 안전 변환 함수
        def sanitize_for_json(obj):
            """Infinity, -Infinity, NaN을 JSON 안전 값으로 변환"""
            import math
            # numpy float 타입도 처리
            if isinstance(obj, (float, np.floating)):
                if math.isinf(float(obj)) or math.isnan(float(obj)):
                    return 0
                return float(obj)  # numpy 타입을 Python float으로 변환
            elif isinstance(obj, np.integer):
                return int(obj)  # numpy 정수를 Python int로 변환
            return obj

        # DataFrame을 dict로 변환 후 Infinity/NaN 처리
        data = df.to_dict('records')
        for row in data:
            for key, value in row.items():
                row[key] = sanitize_for_json(value)

        # 세션에 저장 (선택사항)
        snapshot_id = int(pd.Timestamp.now().timestamp())
        session[f'coupang_snapshot_{snapshot_id}'] = {
            'data': data,
            'summary': summary,
            'created_at': pd.Timestamp.now().isoformat()
        }

        logger.info(f'Coupang data processed successfully: {len(data)} keywords')

        return jsonify({
            'success': True,
            'data': data,
            'summary': summary
        })

    except Exception as e:
        logger.error(f'Coupang file upload failed: {e}')
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': f'처리 중 오류: {str(e)}'}), 500
