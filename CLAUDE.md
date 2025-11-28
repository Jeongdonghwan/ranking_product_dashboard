# 광고 분석 대시보드 구현 가이드

## 프로젝트 개요
mbizsquare.com의 기존 Flask + React 시스템에 **독립적인 광고 분석 대시보드**를 추가합니다.
- 기존 코드 수정 최소화 (iframe 또는 별도 라우트)
- 세션 쿠키 기반 인증 공유
- MariaDB 사용
- 수동 데이터 입력 방식 (Excel/CSV 업로드 + 직접 입력)

---

## 기술 스택
- **Backend**: Flask (기존 활용)
- **Frontend**: HTML + Vanilla JavaScript + Chart.js
- **Database**: MariaDB (기존 DB 활용)
- **AI**: OpenAI GPT-4 API
- **파일 처리**: pandas, openpyxl

---

## 데이터베이스 스키마

```sql
-- 광고 분석 스냅샷 저장
CREATE TABLE ad_analysis_snapshots (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    snapshot_name VARCHAR(255) NOT NULL,
    period_start DATE NOT NULL,
    period_end DATE NOT NULL,
    data_json TEXT NOT NULL COMMENT '원본 데이터 (JSON)',
    metrics_summary JSON COMMENT '요약 지표',
    ai_insights TEXT COMMENT 'AI 생성 인사이트',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    is_saved BOOLEAN DEFAULT FALSE COMMENT '사용자가 저장한 분석',
    tags VARCHAR(255) COMMENT '태그 (쉼표 구분)',
    memo TEXT COMMENT '메모',
    FOREIGN KEY (user_id) REFERENCES users(id),
    INDEX idx_user_date (user_id, period_start, period_end),
    INDEX idx_saved (user_id, is_saved)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 일별 광고 데이터 (원본)
CREATE TABLE ad_daily_data (
    id INT PRIMARY KEY AUTO_INCREMENT,
    snapshot_id INT NOT NULL,
    date DATE NOT NULL,
    campaign_name VARCHAR(255) NOT NULL,
    spend DECIMAL(12, 2) NOT NULL COMMENT '지출액',
    impressions INT DEFAULT 0 COMMENT '노출수',
    clicks INT DEFAULT 0 COMMENT '클릭수',
    conversions INT DEFAULT 0 COMMENT '전환수',
    revenue DECIMAL(12, 2) DEFAULT 0 COMMENT '매출액',
    FOREIGN KEY (snapshot_id) REFERENCES ad_analysis_snapshots(id) ON DELETE CASCADE,
    INDEX idx_snapshot_date (snapshot_id, date),
    INDEX idx_campaign (campaign_name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 캠페인 메모
CREATE TABLE ad_campaign_memos (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    campaign_name VARCHAR(255) NOT NULL,
    memo TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id),
    INDEX idx_user_campaign (user_id, campaign_name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 월별 목표 설정
CREATE TABLE ad_monthly_goals (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    year_month VARCHAR(7) NOT NULL COMMENT 'YYYY-MM',
    budget DECIMAL(12, 2) COMMENT '월 예산',
    target_roas DECIMAL(5, 2) COMMENT '목표 ROAS',
    target_revenue DECIMAL(12, 2) COMMENT '목표 매출',
    FOREIGN KEY (user_id) REFERENCES users(id),
    UNIQUE KEY uk_user_month (user_id, year_month)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

---

## Flask Backend 구조

### 디렉토리 구조
```
/app
├── routes/
│   └── ad_analysis.py          # 광고 분석 API 라우트
├── services/
│   ├── ad_analyzer.py          # 분석 로직
│   └── ai_insights.py          # OpenAI 연동
├── templates/
│   └── ad_dashboard.html       # 대시보드 HTML
└── static/
    └── js/
        └── ad_dashboard.js     # 대시보드 JavaScript
```

### API 엔드포인트

```python
# routes/ad_analysis.py

from flask import Blueprint, render_template, request, jsonify, session
from services.ad_analyzer import AdAnalyzer
from services.ai_insights import AIInsights
import pandas as pd

ad_bp = Blueprint('ad_analysis', __name__)

# 1. 대시보드 메인 페이지
@ad_bp.route('/ad-dashboard')
def dashboard():
    """광고 분석 대시보드 메인 페이지"""
    if 'user_id' not in session:
        return redirect('/login')
    
    user_id = session['user_id']
    # 사용자 정보 가져오기
    user = get_user_info(user_id)
    
    return render_template('ad_dashboard.html', user=user)


# 2. 데이터 업로드 (Excel/CSV)
@ad_bp.route('/api/ad-analysis/upload', methods=['POST'])
def upload_data():
    """
    Excel/CSV 파일 업로드 및 분석
    
    Request:
        - file: Excel/CSV 파일
        - snapshot_name: 분석 이름
        - period_start: 시작일 (YYYY-MM-DD)
        - period_end: 종료일
    
    Response:
        {
            "success": true,
            "snapshot_id": 123,
            "metrics": {...},
            "insights": "AI 생성 인사이트"
        }
    """
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    user_id = session['user_id']
    file = request.files.get('file')
    snapshot_name = request.form.get('snapshot_name', '새 분석')
    
    # 파일 파싱
    if file.filename.endswith('.csv'):
        df = pd.read_csv(file)
    else:
        df = pd.read_excel(file)
    
    # 필수 컬럼 확인
    required_cols = ['date', 'campaign_name', 'spend', 'clicks', 'conversions', 'revenue']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        return jsonify({'error': f'필수 컬럼 누락: {missing_cols}'}), 400
    
    # DB 저장
    analyzer = AdAnalyzer(user_id)
    snapshot_id = analyzer.save_snapshot(df, snapshot_name)
    
    # 지표 계산
    metrics = analyzer.calculate_metrics(snapshot_id)
    
    # AI 인사이트 생성
    ai = AIInsights()
    insights = ai.generate_insights(metrics, df)
    
    # 인사이트 DB 저장
    analyzer.save_insights(snapshot_id, insights)
    
    return jsonify({
        'success': True,
        'snapshot_id': snapshot_id,
        'metrics': metrics,
        'insights': insights
    })


# 3. 수기 데이터 입력
@ad_bp.route('/api/ad-analysis/manual-input', methods=['POST'])
def manual_input():
    """
    수기로 데이터 입력
    
    Request Body:
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
                ...
            ]
        }
    """
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    user_id = session['user_id']
    data = request.json
    
    df = pd.DataFrame(data['data'])
    
    analyzer = AdAnalyzer(user_id)
    snapshot_id = analyzer.save_snapshot(df, data['snapshot_name'])
    metrics = analyzer.calculate_metrics(snapshot_id)
    
    return jsonify({
        'success': True,
        'snapshot_id': snapshot_id,
        'metrics': metrics
    })


# 4. 저장된 분석 목록 조회
@ad_bp.route('/api/ad-analysis/snapshots')
def get_snapshots():
    """
    저장된 분석 목록 조회
    
    Query Params:
        - saved_only: true/false (저장된 것만)
    
    Response:
        {
            "snapshots": [
                {
                    "id": 123,
                    "name": "11월 2주차",
                    "period_start": "2024-11-04",
                    "period_end": "2024-11-10",
                    "avg_roas": 3.5,
                    "total_spend": 5800000,
                    "created_at": "2024-11-11 10:00:00",
                    "tags": "블프,신규캠페인"
                },
                ...
            ]
        }
    """
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    user_id = session['user_id']
    saved_only = request.args.get('saved_only', 'false') == 'true'
    
    analyzer = AdAnalyzer(user_id)
    snapshots = analyzer.get_snapshots(saved_only)
    
    return jsonify({'snapshots': snapshots})


# 5. 특정 분석 상세 조회
@ad_bp.route('/api/ad-analysis/snapshots/<int:snapshot_id>')
def get_snapshot_detail(snapshot_id):
    """
    특정 분석의 상세 데이터 조회
    
    Response:
        {
            "snapshot": {...},
            "daily_data": [...],
            "metrics": {...},
            "insights": "AI 인사이트",
            "campaigns": [...]  # 캠페인별 통계
        }
    """
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    user_id = session['user_id']
    analyzer = AdAnalyzer(user_id)
    
    # 권한 확인
    if not analyzer.check_ownership(snapshot_id):
        return jsonify({'error': 'Forbidden'}), 403
    
    data = analyzer.get_snapshot_detail(snapshot_id)
    
    return jsonify(data)


# 6. 분석 저장/수정
@ad_bp.route('/api/ad-analysis/snapshots/<int:snapshot_id>', methods=['PUT'])
def update_snapshot(snapshot_id):
    """
    분석 저장/수정
    
    Request Body:
        {
            "is_saved": true,
            "snapshot_name": "수정된 이름",
            "tags": "블프,신규",
            "memo": "메모 내용"
        }
    """
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    user_id = session['user_id']
    data = request.json
    
    analyzer = AdAnalyzer(user_id)
    
    if not analyzer.check_ownership(snapshot_id):
        return jsonify({'error': 'Forbidden'}), 403
    
    analyzer.update_snapshot(snapshot_id, data)
    
    return jsonify({'success': True})


# 7. 분석 삭제
@ad_bp.route('/api/ad-analysis/snapshots/<int:snapshot_id>', methods=['DELETE'])
def delete_snapshot(snapshot_id):
    """분석 삭제"""
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    user_id = session['user_id']
    analyzer = AdAnalyzer(user_id)
    
    if not analyzer.check_ownership(snapshot_id):
        return jsonify({'error': 'Forbidden'}), 403
    
    analyzer.delete_snapshot(snapshot_id)
    
    return jsonify({'success': True})


# 8. 기간 비교 분석
@ad_bp.route('/api/ad-analysis/compare')
def compare_periods():
    """
    두 기간 비교 분석
    
    Query Params:
        - snapshot_a: 기준 분석 ID
        - snapshot_b: 비교 분석 ID
    
    Response:
        {
            "comparison": {
                "roas": {"a": 3.5, "b": 3.2, "change": 9, "trend": "up"},
                "ctr": {"a": 2.8, "b": 3.0, "change": -7, "trend": "down"},
                ...
            },
            "summary": "개선 요약 텍스트"
        }
    """
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    snapshot_a = request.args.get('snapshot_a', type=int)
    snapshot_b = request.args.get('snapshot_b', type=int)
    
    user_id = session['user_id']
    analyzer = AdAnalyzer(user_id)
    
    comparison = analyzer.compare_snapshots(snapshot_a, snapshot_b)
    
    return jsonify(comparison)


# 9. 월별 목표 설정/조회
@ad_bp.route('/api/ad-analysis/goals', methods=['GET', 'POST'])
def manage_goals():
    """
    월별 목표 설정/조회
    
    GET - Query Params:
        - year_month: YYYY-MM
    
    POST - Request Body:
        {
            "year_month": "2024-11",
            "budget": 10000000,
            "target_roas": 4.0,
            "target_revenue": 40000000
        }
    """
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    user_id = session['user_id']
    
    if request.method == 'GET':
        year_month = request.args.get('year_month')
        goal = get_monthly_goal(user_id, year_month)
        return jsonify({'goal': goal})
    
    else:  # POST
        data = request.json
        save_monthly_goal(user_id, data)
        return jsonify({'success': True})


# 10. 예산 소진율 계산
@ad_bp.route('/api/ad-analysis/budget-pacing')
def budget_pacing():
    """
    예산 소진율 및 페이싱 분석
    
    Query Params:
        - year_month: YYYY-MM
        - snapshot_id: (optional) 특정 분석 기준
    
    Response:
        {
            "budget": 10000000,
            "spent": 5800000,
            "spent_rate": 58,
            "progress_rate": 40,
            "status": "FAST",  # FAST, SLOW, ON_TRACK
            "projected_end_date": "2024-11-24",
            "suggestion": "일 예산 5만원 감축 권장"
        }
    """
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    user_id = session['user_id']
    year_month = request.args.get('year_month')
    
    analyzer = AdAnalyzer(user_id)
    pacing = analyzer.calculate_budget_pacing(year_month)
    
    return jsonify(pacing)


# 11. 캠페인 메모 관리
@ad_bp.route('/api/ad-analysis/memos', methods=['GET', 'POST'])
def manage_memos():
    """
    캠페인 메모 조회/추가
    
    GET - Query Params:
        - campaign_name: 캠페인명
    
    POST - Request Body:
        {
            "campaign_name": "블프_신규",
            "memo": "소재 #3으로 교체"
        }
    """
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    user_id = session['user_id']
    
    if request.method == 'GET':
        campaign = request.args.get('campaign_name')
        memos = get_campaign_memos(user_id, campaign)
        return jsonify({'memos': memos})
    
    else:  # POST
        data = request.json
        save_memo(user_id, data['campaign_name'], data['memo'])
        return jsonify({'success': True})


# 12. PDF 리포트 생성
@ad_bp.route('/api/ad-analysis/export/pdf/<int:snapshot_id>')
def export_pdf(snapshot_id):
    """PDF 리포트 생성 및 다운로드"""
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    user_id = session['user_id']
    analyzer = AdAnalyzer(user_id)
    
    if not analyzer.check_ownership(snapshot_id):
        return jsonify({'error': 'Forbidden'}), 403
    
    # PDF 생성
    pdf_path = analyzer.generate_pdf_report(snapshot_id)
    
    return send_file(pdf_path, as_attachment=True, download_name=f'ad_report_{snapshot_id}.pdf')


# 13. Excel 리포트 생성
@ad_bp.route('/api/ad-analysis/export/excel/<int:snapshot_id>')
def export_excel(snapshot_id):
    """Excel 리포트 생성 및 다운로드"""
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    user_id = session['user_id']
    analyzer = AdAnalyzer(user_id)
    
    if not analyzer.check_ownership(snapshot_id):
        return jsonify({'error': 'Forbidden'}), 403
    
    # Excel 생성
    excel_path = analyzer.generate_excel_report(snapshot_id)
    
    return send_file(excel_path, as_attachment=True, download_name=f'ad_report_{snapshot_id}.xlsx')


# 14. Excel 템플릿 다운로드
@ad_bp.route('/api/ad-analysis/template/<template_type>')
def download_template(template_type):
    """
    Excel 템플릿 다운로드
    
    template_type: 'naver', 'meta', 'google', 'kakao', 'generic'
    """
    templates = {
        'generic': '/static/templates/ad_template_generic.xlsx',
        'naver': '/static/templates/ad_template_naver.xlsx',
        'meta': '/static/templates/ad_template_meta.xlsx',
    }
    
    template_path = templates.get(template_type, templates['generic'])
    
    return send_file(template_path, as_attachment=True)
```

---

## 서비스 레이어 구현

### services/ad_analyzer.py

```python
"""광고 분석 로직"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
from database import db  # 기존 DB 연결 사용

class AdAnalyzer:
    def __init__(self, user_id):
        self.user_id = user_id
    
    def save_snapshot(self, df, snapshot_name):
        """데이터프레임을 DB에 저장"""
        
        # 기간 추출
        period_start = df['date'].min()
        period_end = df['date'].max()
        
        # 스냅샷 생성
        cursor = db.cursor()
        sql = """
            INSERT INTO ad_analysis_snapshots 
            (user_id, snapshot_name, period_start, period_end, data_json)
            VALUES (%s, %s, %s, %s, %s)
        """
        data_json = df.to_json(orient='records', date_format='iso')
        
        cursor.execute(sql, (
            self.user_id,
            snapshot_name,
            period_start,
            period_end,
            data_json
        ))
        
        snapshot_id = cursor.lastrowid
        
        # 일별 데이터 저장
        for _, row in df.iterrows():
            sql = """
                INSERT INTO ad_daily_data
                (snapshot_id, date, campaign_name, spend, impressions, clicks, conversions, revenue)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(sql, (
                snapshot_id,
                row['date'],
                row['campaign_name'],
                row['spend'],
                row.get('impressions', 0),
                row['clicks'],
                row['conversions'],
                row['revenue']
            ))
        
        db.commit()
        cursor.close()
        
        return snapshot_id
    
    def calculate_metrics(self, snapshot_id):
        """지표 계산"""
        
        cursor = db.cursor(dictionary=True)
        
        # 일별 데이터 조회
        sql = """
            SELECT * FROM ad_daily_data
            WHERE snapshot_id = %s
            ORDER BY date
        """
        cursor.execute(sql, (snapshot_id,))
        data = cursor.fetchall()
        
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
            'avg_roas': round(total_revenue / total_spend, 2) if total_spend > 0 else 0,
            'avg_ctr': round((total_clicks / total_impressions * 100), 2) if total_impressions > 0 else 0,
            'avg_cpc': round(total_spend / total_clicks, 0) if total_clicks > 0 else 0,
            'avg_cpa': round(total_spend / total_conversions, 0) if total_conversions > 0 else 0,
            'cvr': round((total_conversions / total_clicks * 100), 2) if total_clicks > 0 else 0,
            'avg_order_value': round(total_revenue / total_conversions, 0) if total_conversions > 0 else 0,
            
            # 캠페인별 통계
            'campaigns': self._calculate_campaign_metrics(df),
            
            # 일별 트렌드
            'daily_trend': self._calculate_daily_trend(df),
        }
        
        # metrics_summary 업데이트
        sql = """
            UPDATE ad_analysis_snapshots
            SET metrics_summary = %s
            WHERE id = %s
        """
        cursor.execute(sql, (json.dumps(metrics), snapshot_id))
        db.commit()
        cursor.close()
        
        return metrics
    
    def _calculate_campaign_metrics(self, df):
        """캠페인별 지표 계산"""
        
        campaign_stats = df.groupby('campaign_name').agg({
            'spend': 'sum',
            'revenue': 'sum',
            'clicks': 'sum',
            'conversions': 'sum',
            'impressions': 'sum'
        }).reset_index()
        
        campaign_stats['roas'] = (campaign_stats['revenue'] / campaign_stats['spend']).round(2)
        campaign_stats['ctr'] = (campaign_stats['clicks'] / campaign_stats['impressions'] * 100).round(2)
        campaign_stats['cpa'] = (campaign_stats['spend'] / campaign_stats['conversions']).round(0)
        campaign_stats['cvr'] = (campaign_stats['conversions'] / campaign_stats['clicks'] * 100).round(2)
        
        # ROAS 순위 계산
        campaign_stats = campaign_stats.sort_values('roas', ascending=False)
        campaign_stats['rank'] = range(1, len(campaign_stats) + 1)
        
        # 상태 판정 (ROAS 기준)
        campaign_stats['status'] = campaign_stats['roas'].apply(
            lambda x: 'excellent' if x >= 4.0 else ('good' if x >= 3.0 else 'poor')
        )
        
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
        
        daily['roas'] = (daily['revenue'] / daily['spend']).round(2)
        daily['ctr'] = (daily['clicks'] / daily['impressions'] * 100).round(2)
        daily['cvr'] = (daily['conversions'] / daily['clicks'] * 100).round(2)
        
        # 7일 이동평균 계산
        daily['roas_ma7'] = daily['roas'].rolling(window=7, min_periods=1).mean().round(2)
        
        return daily.to_dict('records')
    
    def compare_snapshots(self, snapshot_a_id, snapshot_b_id):
        """두 분석 비교"""
        
        metrics_a = self.get_snapshot_metrics(snapshot_a_id)
        metrics_b = self.get_snapshot_metrics(snapshot_b_id)
        
        comparison = {}
        
        for key in ['avg_roas', 'avg_ctr', 'avg_cpa', 'cvr', 'avg_cpc']:
            val_a = metrics_a[key]
            val_b = metrics_b[key]
            
            if val_b > 0:
                change_pct = round(((val_a - val_b) / val_b * 100), 1)
            else:
                change_pct = 0
            
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
            'snapshot_a': self.get_snapshot_info(snapshot_a_id),
            'snapshot_b': self.get_snapshot_info(snapshot_b_id)
        }
    
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
        """예산 소진율 계산"""
        
        # 월별 목표 조회
        goal = self.get_monthly_goal(year_month)
        if not goal or not goal.get('budget'):
            return {'error': '월별 예산이 설정되지 않았습니다'}
        
        budget = goal['budget']
        
        # 해당 월의 지출 합계
        cursor = db.cursor(dictionary=True)
        sql = """
            SELECT SUM(spend) as total_spend
            FROM ad_daily_data d
            JOIN ad_analysis_snapshots s ON d.snapshot_id = s.id
            WHERE s.user_id = %s
            AND DATE_FORMAT(d.date, '%Y-%m') = %s
        """
        cursor.execute(sql, (self.user_id, year_month))
        result = cursor.fetchone()
        cursor.close()
        
        spent = result['total_spend'] or 0
        
        # 진행률 계산
        year, month = map(int, year_month.split('-'))
        today = datetime.now()
        
        if today.year == year and today.month == month:
            days_in_month = (datetime(year, month + 1, 1) - timedelta(days=1)).day if month < 12 else 31
            days_passed = today.day
        else:
            # 과거 월
            days_in_month = (datetime(year, month + 1, 1) - timedelta(days=1)).day if month < 12 else 31
            days_passed = days_in_month
        
        progress_rate = round((days_passed / days_in_month * 100), 1)
        spent_rate = round((spent / budget * 100), 1)
        
        # 페이싱 판정
        if spent_rate > progress_rate * 1.1:
            status = 'FAST'
            # 예상 소진일 계산
            daily_avg = spent / days_passed if days_passed > 0 else 0
            projected_days = int(budget / daily_avg) if daily_avg > 0 else days_in_month
            projected_end_date = (datetime(year, month, 1) + timedelta(days=projected_days - 1)).strftime('%Y-%m-%d')
            
            # 조정 제안
            remaining_days = days_in_month - days_passed
            remaining_budget = budget - spent
            suggested_daily = int(remaining_budget / remaining_days) if remaining_days > 0 else 0
            current_daily = int(daily_avg)
            adjustment = current_daily - suggested_daily
            
            suggestion = f"일 예산 {adjustment:,}원 감축 권장"
            
        elif spent_rate < progress_rate * 0.9:
            status = 'SLOW'
            projected_end_date = f"{year_month}-{days_in_month}"
            
            remaining_days = days_in_month - days_passed
            remaining_budget = budget - spent
            suggested_daily = int(remaining_budget / remaining_days) if remaining_days > 0 else 0
            daily_avg = spent / days_passed if days_passed > 0 else 0
            adjustment = suggested_daily - int(daily_avg)
            
            suggestion = f"일 예산 {adjustment:,}원 증액 권장"
            
        else:
            status = 'ON_TRACK'
            projected_end_date = f"{year_month}-{days_in_month}"
            suggestion = "정상 진행 중"
        
        return {
            'budget': float(budget),
            'spent': float(spent),
            'spent_rate': spent_rate,
            'progress_rate': progress_rate,
            'status': status,
            'projected_end_date': projected_end_date,
            'suggestion': suggestion,
            'days_passed': days_passed,
            'days_total': days_in_month
        }
    
    def get_snapshot_metrics(self, snapshot_id):
        """스냅샷의 metrics_summary 조회"""
        cursor = db.cursor(dictionary=True)
        sql = "SELECT metrics_summary FROM ad_analysis_snapshots WHERE id = %s"
        cursor.execute(sql, (snapshot_id,))
        result = cursor.fetchone()
        cursor.close()
        
        if result and result['metrics_summary']:
            return json.loads(result['metrics_summary'])
        return {}
    
    def get_snapshot_info(self, snapshot_id):
        """스냅샷 기본 정보 조회"""
        cursor = db.cursor(dictionary=True)
        sql = """
            SELECT id, snapshot_name, period_start, period_end
            FROM ad_analysis_snapshots
            WHERE id = %s
        """
        cursor.execute(sql, (snapshot_id,))
        result = cursor.fetchone()
        cursor.close()
        return result
    
    def get_monthly_goal(self, year_month):
        """월별 목표 조회"""
        cursor = db.cursor(dictionary=True)
        sql = """
            SELECT * FROM ad_monthly_goals
            WHERE user_id = %s AND year_month = %s
        """
        cursor.execute(sql, (self.user_id, year_month))
        result = cursor.fetchone()
        cursor.close()
        return result
    
    def check_ownership(self, snapshot_id):
        """스냅샷 소유권 확인"""
        cursor = db.cursor()
        sql = "SELECT user_id FROM ad_analysis_snapshots WHERE id = %s"
        cursor.execute(sql, (snapshot_id,))
        result = cursor.fetchone()
        cursor.close()
        
        return result and result[0] == self.user_id
```

### services/ai_insights.py

```python
"""AI 인사이트 생성"""

import openai
import json

class AIInsights:
    def __init__(self):
        # OpenAI API 키 설정 (환경변수에서 로드)
        openai.api_key = os.getenv('OPENAI_API_KEY')
    
    def generate_insights(self, metrics, df):
        """AI 인사이트 생성"""
        
        # 프롬프트 생성
        prompt = self._create_prompt(metrics, df)
        
        try:
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "당신은 10년 경력의 디지털 마케팅 전문가입니다. 광고 데이터를 분석하고 실행 가능한 조언을 제공합니다."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=1500
            )
            
            insights = response.choices[0].message.content
            return insights
            
        except Exception as e:
            return f"AI 인사이트 생성 실패: {str(e)}"
    
    def _create_prompt(self, metrics, df):
        """프롬프트 생성"""
        
        # 캠페인별 ROAS 정리
        campaigns = metrics.get('campaigns', [])
        campaign_text = "\n".join([
            f"- {c['campaign_name']}: ROAS {c['roas']}, 지출 {c['spend']:,.0f}원"
            for c in campaigns[:10]  # 상위 10개
        ])
        
        # 일별 트렌드 요약
        daily = metrics.get('daily_trend', [])
        if len(daily) >= 7:
            recent_roas = [d['roas'] for d in daily[-7:]]
            roas_trend = "상승" if recent_roas[-1] > recent_roas[0] else "하락"
        else:
            roas_trend = "데이터 부족"
        
        prompt = f"""
다음 광고 데이터를 분석해주세요:

## 전체 지표
- 총 지출: {metrics['total_spend']:,.0f}원
- 총 매출: {metrics['total_revenue']:,.0f}원
- 평균 ROAS: {metrics['avg_roas']}
- 평균 CTR: {metrics['avg_ctr']}%
- 평균 CPA: {metrics['avg_cpa']:,.0f}원
- 전환율: {metrics['cvr']}%
- 객단가: {metrics['avg_order_value']:,.0f}원

## 캠페인별 성과 (ROAS 순)
{campaign_text}

## 최근 7일 트렌드
- ROAS: {roas_trend} 추세

다음 형식으로 작성해주세요:

### 📊 3줄 요약
1. ...
2. ...
3. ...

### 🔍 주요 발견사항
- **우수 캠페인**: ...
- **개선 필요**: ...
- **특이사항**: ...

### 💡 즉시 실행 가능한 액션 (우선순위 순)
1. [높음] ...
2. [높음] ...
3. [중간] ...
4. [중간] ...
5. [낮음] ...

### 📈 예산 재배분 제안
- ...

**중요**: 구체적인 수치와 명확한 근거를 포함하세요. 마케터가 바로 실행할 수 있는 내용이어야 합니다.
"""
        
        return prompt
```

---

## Frontend 구현

### templates/ad_dashboard.html

```html
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>광고 분석 대시보드</title>
    
    <!-- Chart.js -->
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0"></script>
    <script src="https://cdn.jsdelivr.net/npm/chartjs-adapter-date-fns@3.0.0"></script>
    
    <!-- XLSX (Excel 처리) -->
    <script src="https://cdn.jsdelivr.net/npm/xlsx@0.18.5/dist/xlsx.full.min.js"></script>
    
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Noto Sans KR', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            background: #f5f7fa;
            color: #2c3e50;
        }
        
        .container {
            max-width: 1400px;
            margin: 0 auto;
            padding: 20px;
        }
        
        header {
            background: white;
            padding: 20px;
            border-radius: 12px;
            margin-bottom: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        
        h1 {
            font-size: 28px;
            color: #2c3e50;
            margin-bottom: 10px;
        }
        
        .tabs {
            display: flex;
            gap: 10px;
            margin-top: 15px;
        }
        
        .tab {
            padding: 10px 20px;
            background: #ecf0f1;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            font-size: 14px;
            transition: all 0.3s;
        }
        
        .tab.active {
            background: #3498db;
            color: white;
        }
        
        .tab:hover {
            background: #3498db;
            color: white;
        }
        
        .section {
            background: white;
            padding: 25px;
            border-radius: 12px;
            margin-bottom: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        
        .section-title {
            font-size: 20px;
            font-weight: 600;
            margin-bottom: 20px;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        
        /* 업로드 섹션 */
        .upload-area {
            border: 2px dashed #bdc3c7;
            border-radius: 8px;
            padding: 40px;
            text-align: center;
            background: #f8f9fa;
            cursor: pointer;
            transition: all 0.3s;
        }
        
        .upload-area:hover {
            border-color: #3498db;
            background: #e3f2fd;
        }
        
        .upload-area.dragging {
            border-color: #2ecc71;
            background: #d5f4e6;
        }
        
        .button-group {
            display: flex;
            gap: 10px;
            margin-top: 15px;
            justify-content: center;
        }
        
        .btn {
            padding: 10px 20px;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            font-size: 14px;
            font-weight: 500;
            transition: all 0.3s;
        }
        
        .btn-primary {
            background: #3498db;
            color: white;
        }
        
        .btn-primary:hover {
            background: #2980b9;
        }
        
        .btn-secondary {
            background: #95a5a6;
            color: white;
        }
        
        .btn-success {
            background: #2ecc71;
            color: white;
        }
        
        .btn-danger {
            background: #e74c3c;
            color: white;
        }
        
        /* 메트릭스 카드 */
        .metrics-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-bottom: 20px;
        }
        
        .metric-card {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
            border-radius: 12px;
            color: white;
        }
        
        .metric-card.green {
            background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
        }
        
        .metric-card.blue {
            background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
        }
        
        .metric-card.orange {
            background: linear-gradient(135deg, #fa709a 0%, #fee140 100%);
        }
        
        .metric-label {
            font-size: 14px;
            opacity: 0.9;
            margin-bottom: 5px;
        }
        
        .metric-value {
            font-size: 32px;
            font-weight: 700;
        }
        
        .metric-change {
            font-size: 12px;
            margin-top: 5px;
        }
        
        /* 차트 */
        .chart-container {
            position: relative;
            height: 400px;
            margin: 20px 0;
        }
        
        .charts-grid {
            display: grid;
            grid-template-columns: 2fr 1fr;
            gap: 20px;
        }
        
        /* 테이블 */
        table {
            width: 100%;
            border-collapse: collapse;
        }
        
        th, td {
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ecf0f1;
        }
        
        th {
            background: #f8f9fa;
            font-weight: 600;
            color: #7f8c8d;
            font-size: 13px;
        }
        
        td {
            font-size: 14px;
        }
        
        tr:hover {
            background: #f8f9fa;
        }
        
        /* 상태 배지 */
        .status-badge {
            display: inline-block;
            padding: 4px 12px;
            border-radius: 12px;
            font-size: 12px;
            font-weight: 600;
        }
        
        .status-excellent {
            background: #d4edda;
            color: #155724;
        }
        
        .status-good {
            background: #fff3cd;
            color: #856404;
        }
        
        .status-poor {
            background: #f8d7da;
            color: #721c24;
        }
        
        /* AI 인사이트 */
        .insights-box {
            background: #f8f9fa;
            border-left: 4px solid #3498db;
            padding: 20px;
            border-radius: 8px;
            white-space: pre-wrap;
            line-height: 1.6;
        }
        
        /* 저장된 분석 목록 */
        .snapshot-list {
            display: grid;
            gap: 15px;
        }
        
        .snapshot-item {
            background: #f8f9fa;
            padding: 15px;
            border-radius: 8px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            transition: all 0.3s;
        }
        
        .snapshot-item:hover {
            background: #e9ecef;
            transform: translateX(5px);
        }
        
        .snapshot-info h4 {
            margin-bottom: 5px;
            color: #2c3e50;
        }
        
        .snapshot-info p {
            font-size: 13px;
            color: #7f8c8d;
        }
        
        .snapshot-actions {
            display: flex;
            gap: 10px;
        }
        
        /* 비교 테이블 */
        .comparison-table {
            width: 100%;
        }
        
        .comparison-table td {
            text-align: center;
        }
        
        .comparison-table .trend-up {
            color: #2ecc71;
            font-weight: 600;
        }
        
        .comparison-table .trend-down {
            color: #e74c3c;
            font-weight: 600;
        }
        
        /* 로딩 */
        .loading {
            text-align: center;
            padding: 40px;
        }
        
        .spinner {
            border: 4px solid #f3f3f3;
            border-top: 4px solid #3498db;
            border-radius: 50%;
            width: 40px;
            height: 40px;
            animation: spin 1s linear infinite;
            margin: 0 auto;
        }
        
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        
        /* 모달 */
        .modal {
            display: none;
            position: fixed;
            z-index: 1000;
            left: 0;
            top: 0;
            width: 100%;
            height: 100%;
            background: rgba(0,0,0,0.5);
        }
        
        .modal-content {
            background: white;
            margin: 10% auto;
            padding: 30px;
            border-radius: 12px;
            width: 90%;
            max-width: 500px;
        }
        
        .modal-header {
            font-size: 20px;
            font-weight: 600;
            margin-bottom: 20px;
        }
        
        .form-group {
            margin-bottom: 15px;
        }
        
        .form-group label {
            display: block;
            margin-bottom: 5px;
            font-weight: 500;
        }
        
        .form-group input,
        .form-group textarea {
            width: 100%;
            padding: 10px;
            border: 1px solid #ddd;
            border-radius: 6px;
            font-size: 14px;
        }
        
        /* 히든 */
        .hidden {
            display: none;
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>📊 광고 분석 대시보드</h1>
            <p>환영합니다, <strong>{{ user.name }}</strong>님</p>
            
            <div class="tabs">
                <button class="tab active" data-tab="upload">데이터 입력</button>
                <button class="tab" data-tab="analysis">분석 결과</button>
                <button class="tab" data-tab="compare">기간 비교</button>
                <button class="tab" data-tab="saved">저장된 분석</button>
                <button class="tab" data-tab="goals">목표 관리</button>
            </div>
        </header>
        
        <!-- 탭 1: 데이터 입력 -->
        <div id="tab-upload" class="tab-content">
            <div class="section">
                <h2 class="section-title">📤 데이터 업로드</h2>
                
                <div class="upload-area" id="uploadArea">
                    <p style="font-size: 18px; margin-bottom: 10px;">📁 Excel/CSV 파일을 드래그하거나 클릭하세요</p>
                    <p style="color: #7f8c8d; font-size: 14px;">지원 형식: .xlsx, .xls, .csv</p>
                    <input type="file" id="fileInput" accept=".xlsx,.xls,.csv" style="display: none;">
                </div>
                
                <div class="button-group">
                    <button class="btn btn-secondary" onclick="downloadTemplate('generic')">📥 범용 템플릿</button>
                    <button class="btn btn-secondary" onclick="downloadTemplate('naver')">📥 네이버 템플릿</button>
                    <button class="btn btn-secondary" onclick="downloadTemplate('meta')">📥 메타 템플릿</button>
                </div>
                
                <div id="uploadProgress" class="hidden" style="margin-top: 20px;">
                    <div class="loading">
                        <div class="spinner"></div>
                        <p style="margin-top: 15px;">데이터 처리 중...</p>
                    </div>
                </div>
            </div>
            
            <div class="section">
                <h2 class="section-title">✏️ 수기 입력</h2>
                <button class="btn btn-primary" onclick="openManualInputModal()">일별 데이터 입력하기</button>
            </div>
        </div>
        
        <!-- 탭 2: 분석 결과 -->
        <div id="tab-analysis" class="tab-content hidden">
            <div class="section">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
                    <h2 class="section-title">📊 주요 지표</h2>
                    <div>
                        <button class="btn btn-success" onclick="saveCurrentAnalysis()">💾 이 분석 저장</button>
                        <button class="btn btn-secondary" onclick="exportPDF()">📄 PDF</button>
                        <button class="btn btn-secondary" onclick="exportExcel()">📊 Excel</button>
                    </div>
                </div>
                
                <div class="metrics-grid" id="metricsGrid">
                    <!-- 동적 생성 -->
                </div>
            </div>
            
            <div class="charts-grid">
                <div class="section">
                    <h2 class="section-title">📈 일별 트렌드</h2>
                    <div class="chart-container">
                        <canvas id="trendChart"></canvas>
                    </div>
                </div>
                
                <div class="section">
                    <h2 class="section-title">💡 AI 인사이트</h2>
                    <div id="aiInsights" class="insights-box">
                        데이터를 업로드하면 AI 분석이 표시됩니다.
                    </div>
                </div>
            </div>
            
            <div class="section">
                <h2 class="section-title">🏆 캠페인별 성과</h2>
                <table id="campaignTable">
                    <thead>
                        <tr>
                            <th>순위</th>
                            <th>캠페인명</th>
                            <th>ROAS</th>
                            <th>CTR</th>
                            <th>CPA</th>
                            <th>지출액</th>
                            <th>상태</th>
                        </tr>
                    </thead>
                    <tbody id="campaignTableBody">
                        <!-- 동적 생성 -->
                    </tbody>
                </table>
            </div>
        </div>
        
        <!-- 탭 3: 기간 비교 -->
        <div id="tab-compare" class="tab-content hidden">
            <div class="section">
                <h2 class="section-title">📊 기간 비교</h2>
                
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 20px;">
                    <div>
                        <label>기준 분석 (A)</label>
                        <select id="compareSnapshotA" class="form-control">
                            <option value="">선택하세요</option>
                        </select>
                    </div>
                    <div>
                        <label>비교 분석 (B)</label>
                        <select id="compareSnapshotB" class="form-control">
                            <option value="">선택하세요</option>
                        </select>
                    </div>
                </div>
                
                <button class="btn btn-primary" onclick="compareAnalysis()">비교 분석 시작</button>
                
                <div id="comparisonResult" class="hidden" style="margin-top: 30px;">
                    <h3>비교 결과</h3>
                    <div id="comparisonSummary" class="insights-box" style="margin: 20px 0;"></div>
                    
                    <table class="comparison-table">
                        <thead>
                            <tr>
                                <th>지표</th>
                                <th>현재(A)</th>
                                <th>이전(B)</th>
                                <th>변화</th>
                            </tr>
                        </thead>
                        <tbody id="comparisonTableBody">
                            <!-- 동적 생성 -->
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
        
        <!-- 탭 4: 저장된 분석 -->
        <div id="tab-saved" class="tab-content hidden">
            <div class="section">
                <h2 class="section-title">📂 저장된 분석</h2>
                <div class="snapshot-list" id="snapshotList">
                    <!-- 동적 생성 -->
                </div>
            </div>
        </div>
        
        <!-- 탭 5: 목표 관리 -->
        <div id="tab-goals" class="tab-content hidden">
            <div class="section">
                <h2 class="section-title">🎯 월별 목표 설정</h2>
                
                <div class="form-group">
                    <label>대상 월</label>
                    <input type="month" id="goalMonth" value="">
                </div>
                
                <div class="form-group">
                    <label>월 예산 (원)</label>
                    <input type="number" id="goalBudget" placeholder="10000000">
                </div>
                
                <div class="form-group">
                    <label>목표 ROAS</label>
                    <input type="number" step="0.1" id="goalRoas" placeholder="4.0">
                </div>
                
                <button class="btn btn-primary" onclick="saveGoal()">목표 저장</button>
            </div>
            
            <div class="section">
                <h2 class="section-title">💰 예산 소진 현황</h2>
                <div id="budgetPacing">
                    <!-- 동적 생성 -->
                </div>
            </div>
        </div>
    </div>
    
    <!-- 저장 모달 -->
    <div id="saveModal" class="modal">
        <div class="modal-content">
            <h3 class="modal-header">💾 분석 저장하기</h3>
            
            <div class="form-group">
                <label>분석 이름</label>
                <input type="text" id="saveName" placeholder="예: 11월 2주차">
            </div>
            
            <div class="form-group">
                <label>태그 (쉼표로 구분)</label>
                <input type="text" id="saveTags" placeholder="예: 블프,신규캠페인">
            </div>
            
            <div class="form-group">
                <label>메모</label>
                <textarea id="saveMemo" rows="3" placeholder="특이사항이나 참고사항을 입력하세요"></textarea>
            </div>
            
            <div class="button-group">
                <button class="btn btn-primary" onclick="confirmSave()">저장</button>
                <button class="btn btn-secondary" onclick="closeSaveModal()">취소</button>
            </div>
        </div>
    </div>
    
    <!-- 수기 입력 모달 -->
    <div id="manualInputModal" class="modal">
        <div class="modal-content">
            <h3 class="modal-header">✏️ 일별 데이터 입력</h3>
            
            <div class="form-group">
                <label>날짜</label>
                <input type="date" id="manualDate">
            </div>
            
            <div class="form-group">
                <label>캠페인명</label>
                <input type="text" id="manualCampaign" placeholder="예: 블프_신규">
            </div>
            
            <div class="form-group">
                <label>지출액 (원)</label>
                <input type="number" id="manualSpend" placeholder="150000">
            </div>
            
            <div class="form-group">
                <label>클릭수</label>
                <input type="number" id="manualClicks" placeholder="1200">
            </div>
            
            <div class="form-group">
                <label>전환수</label>
                <input type="number" id="manualConversions" placeholder="48">
            </div>
            
            <div class="form-group">
                <label>매출액 (원)</label>
                <input type="number" id="manualRevenue" placeholder="540000">
            </div>
            
            <div class="button-group">
                <button class="btn btn-primary" onclick="addManualData()">추가</button>
                <button class="btn btn-success" onclick="submitManualData()">완료</button>
                <button class="btn btn-secondary" onclick="closeManualInputModal()">취소</button>
            </div>
            
            <div id="manualDataPreview" style="margin-top: 20px;">
                <h4>입력된 데이터: <span id="manualDataCount">0</span>건</h4>
            </div>
        </div>
    </div>
    
    <script src="/static/js/ad_dashboard.js"></script>
</body>
</html>
```

### static/js/ad_dashboard.js

```javascript
// 전역 변수
let currentSnapshotId = null;
let currentMetrics = null;
let trendChart = null;
let manualDataBuffer = [];

// 페이지 로드 시 실행
document.addEventListener('DOMContentLoaded', function() {
    initTabs();
    initUpload();
    loadSnapshots();
    
    // 현재 월 자동 설정
    const today = new Date();
    const yearMonth = today.toISOString().slice(0, 7);
    document.getElementById('goalMonth').value = yearMonth;
});

// 탭 전환
function initTabs() {
    const tabs = document.querySelectorAll('.tab');
    const tabContents = document.querySelectorAll('.tab-content');
    
    tabs.forEach(tab => {
        tab.addEventListener('click', function() {
            // 모든 탭 비활성화
            tabs.forEach(t => t.classList.remove('active'));
            tabContents.forEach(tc => tc.classList.add('hidden'));
            
            // 클릭한 탭 활성화
            this.classList.add('active');
            const tabName = this.dataset.tab;
            document.getElementById(`tab-${tabName}`).classList.remove('hidden');
            
            // 저장된 분석 탭이면 목록 새로고침
            if (tabName === 'saved') {
                loadSnapshots();
            }
        });
    });
}

// 파일 업로드 초기화
function initUpload() {
    const uploadArea = document.getElementById('uploadArea');
    const fileInput = document.getElementById('fileInput');
    
    // 클릭 시 파일 선택
    uploadArea.addEventListener('click', () => {
        fileInput.click();
    });
    
    // 파일 선택 시
    fileInput.addEventListener('change', (e) => {
        if (e.target.files.length > 0) {
            uploadFile(e.target.files[0]);
        }
    });
    
    // 드래그 앤 드롭
    uploadArea.addEventListener('dragover', (e) => {
        e.preventDefault();
        uploadArea.classList.add('dragging');
    });
    
    uploadArea.addEventListener('dragleave', () => {
        uploadArea.classList.remove('dragging');
    });
    
    uploadArea.addEventListener('drop', (e) => {
        e.preventDefault();
        uploadArea.classList.remove('dragging');
        
        if (e.dataTransfer.files.length > 0) {
            uploadFile(e.dataTransfer.files[0]);
        }
    });
}

// 파일 업로드 처리
async function uploadFile(file) {
    // 진행 표시
    document.getElementById('uploadProgress').classList.remove('hidden');
    
    const formData = new FormData();
    formData.append('file', file);
    formData.append('snapshot_name', `분석 ${new Date().toLocaleDateString()}`);
    
    try {
        const response = await fetch('/api/ad-analysis/upload', {
            method: 'POST',
            body: formData,
            credentials: 'same-origin'
        });
        
        const result = await response.json();
        
        if (result.success) {
            // 분석 결과 저장
            currentSnapshotId = result.snapshot_id;
            currentMetrics = result.metrics;
            
            // 분석 탭으로 전환
            document.querySelector('[data-tab="analysis"]').click();
            
            // 결과 표시
            displayMetrics(result.metrics);
            displayChart(result.metrics.daily_trend);
            displayCampaigns(result.metrics.campaigns);
            displayInsights(result.insights);
            
            alert('✅ 분석 완료!');
        } else {
            alert('❌ 업로드 실패: ' + result.error);
        }
    } catch (error) {
        console.error('Upload error:', error);
        alert('❌ 업로드 중 오류가 발생했습니다.');
    } finally {
        document.getElementById('uploadProgress').classList.add('hidden');
    }
}

// 메트릭스 표시
function displayMetrics(metrics) {
    const grid = document.getElementById('metricsGrid');
    
    const metricCards = [
        { label: 'ROAS', value: metrics.avg_roas.toFixed(2), class: 'green' },
        { label: 'CTR', value: metrics.avg_ctr.toFixed(2) + '%', class: 'blue' },
        { label: 'CPA', value: metrics.avg_cpa.toLocaleString() + '원', class: 'orange' },
        { label: '전환율', value: metrics.cvr.toFixed(2) + '%', class: '' },
        { label: '총 지출', value: (metrics.total_spend / 10000).toFixed(0) + '만원', class: '' },
        { label: '총 매출', value: (metrics.total_revenue / 10000).toFixed(0) + '만원', class: 'green' }
    ];
    
    grid.innerHTML = metricCards.map(card => `
        <div class="metric-card ${card.class}">
            <div class="metric-label">${card.label}</div>
            <div class="metric-value">${card.value}</div>
        </div>
    `).join('');
}

// 차트 표시
function displayChart(dailyData) {
    const ctx = document.getElementById('trendChart').getContext('2d');
    
    // 기존 차트 제거
    if (trendChart) {
        trendChart.destroy();
    }
    
    const dates = dailyData.map(d => d.date);
    const roasData = dailyData.map(d => d.roas);
    const ctrData = dailyData.map(d => d.ctr);
    const spendData = dailyData.map(d => d.spend / 10000); // 만원 단위
    
    trendChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: dates,
            datasets: [
                {
                    label: 'ROAS',
                    data: roasData,
                    borderColor: 'rgb(46, 204, 113)',
                    backgroundColor: 'rgba(46, 204, 113, 0.1)',
                    yAxisID: 'y',
                    tension: 0.4
                },
                {
                    label: 'CTR (%)',
                    data: ctrData,
                    borderColor: 'rgb(52, 152, 219)',
                    backgroundColor: 'rgba(52, 152, 219, 0.1)',
                    yAxisID: 'y1',
                    tension: 0.4
                },
                {
                    label: '지출 (만원)',
                    data: spendData,
                    type: 'bar',
                    backgroundColor: 'rgba(155, 89, 182, 0.3)',
                    borderColor: 'rgb(155, 89, 182)',
                    yAxisID: 'y2'
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: {
                mode: 'index',
                intersect: false
            },
            plugins: {
                title: {
                    display: true,
                    text: '일별 성과 트렌드',
                    font: { size: 16 }
                },
                legend: {
                    position: 'top'
                }
            },
            scales: {
                y: {
                    type: 'linear',
                    position: 'left',
                    title: { display: true, text: 'ROAS' }
                },
                y1: {
                    type: 'linear',
                    position: 'right',
                    title: { display: true, text: 'CTR (%)' },
                    grid: { drawOnChartArea: false }
                },
                y2: {
                    type: 'linear',
                    position: 'right',
                    title: { display: true, text: '지출 (만원)' },
                    grid: { drawOnChartArea: false }
                }
            }
        }
    });
}

// 캠페인 테이블 표시
function displayCampaigns(campaigns) {
    const tbody = document.getElementById('campaignTableBody');
    
    tbody.innerHTML = campaigns.map(c => {
        let statusClass = 'status-excellent';
        let statusText = '우수';
        
        if (c.status === 'good') {
            statusClass = 'status-good';
            statusText = '보통';
        } else if (c.status === 'poor') {
            statusClass = 'status-poor';
            statusText = '개선필요';
        }
        
        return `
            <tr>
                <td>${c.rank}</td>
                <td>${c.campaign_name}</td>
                <td><strong>${c.roas.toFixed(2)}</strong></td>
                <td>${c.ctr.toFixed(2)}%</td>
                <td>${c.cpa.toLocaleString()}원</td>
                <td>${(c.spend / 10000).toFixed(0)}만원</td>
                <td><span class="status-badge ${statusClass}">${statusText}</span></td>
            </tr>
        `;
    }).join('');
}

// AI 인사이트 표시
function displayInsights(insights) {
    document.getElementById('aiInsights').textContent = insights;
}

// 분석 저장
function saveCurrentAnalysis() {
    if (!currentSnapshotId) {
        alert('저장할 분석이 없습니다.');
        return;
    }
    
    document.getElementById('saveModal').style.display = 'block';
}

function closeSaveModal() {
    document.getElementById('saveModal').style.display = 'none';
}

async function confirmSave() {
    const name = document.getElementById('saveName').value;
    const tags = document.getElementById('saveTags').value;
    const memo = document.getElementById('saveMemo').value;
    
    if (!name) {
        alert('분석 이름을 입력하세요.');
        return;
    }
    
    try {
        const response = await fetch(`/api/ad-analysis/snapshots/${currentSnapshotId}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'same-origin',
            body: JSON.stringify({
                is_saved: true,
                snapshot_name: name,
                tags: tags,
                memo: memo
            })
        });
        
        const result = await response.json();
        
        if (result.success) {
            alert('✅ 저장 완료!');
            closeSaveModal();
            loadSnapshots();
        }
    } catch (error) {
        console.error('Save error:', error);
        alert('❌ 저장 실패');
    }
}

// 저장된 분석 목록 로드
async function loadSnapshots() {
    try {
        const response = await fetch('/api/ad-analysis/snapshots?saved_only=true', {
            credentials: 'same-origin'
        });
        
        const result = await response.json();
        const snapshots = result.snapshots;
        
        // 목록 표시
        const listContainer = document.getElementById('snapshotList');
        
        if (snapshots.length === 0) {
            listContainer.innerHTML = '<p style="text-align:center; color:#7f8c8d;">저장된 분석이 없습니다.</p>';
        } else {
            listContainer.innerHTML = snapshots.map(s => `
                <div class="snapshot-item">
                    <div class="snapshot-info">
                        <h4>${s.snapshot_name}</h4>
                        <p>${s.period_start} ~ ${s.period_end} | ROAS ${s.metrics_summary?.avg_roas || 'N/A'} | 지출 ${((s.metrics_summary?.total_spend || 0) / 10000).toFixed(0)}만원</p>
                        ${s.tags ? `<p style="color:#3498db;">🏷️ ${s.tags}</p>` : ''}
                    </div>
                    <div class="snapshot-actions">
                        <button class="btn btn-primary" onclick="loadSnapshot(${s.id})">열기</button>
                        <button class="btn btn-danger" onclick="deleteSnapshot(${s.id})">삭제</button>
                    </div>
                </div>
            `).join('');
        }
        
        // 비교 셀렉트박스 업데이트
        updateCompareSelects(snapshots);
        
    } catch (error) {
        console.error('Load snapshots error:', error);
    }
}

// 스냅샷 불러오기
async function loadSnapshot(snapshotId) {
    try {
        const response = await fetch(`/api/ad-analysis/snapshots/${snapshotId}`, {
            credentials: 'same-origin'
        });
        
        const data = await response.json();
        
        currentSnapshotId = snapshotId;
        currentMetrics = data.metrics;
        
        // 분석 탭으로 전환
        document.querySelector('[data-tab="analysis"]').click();
        
        // 결과 표시
        displayMetrics(data.metrics);
        displayChart(data.metrics.daily_trend);
        displayCampaigns(data.metrics.campaigns);
        displayInsights(data.insights);
        
    } catch (error) {
        console.error('Load snapshot error:', error);
        alert('불러오기 실패');
    }
}

// 스냅샷 삭제
async function deleteSnapshot(snapshotId) {
    if (!confirm('정말 삭제하시겠습니까?')) return;
    
    try {
        const response = await fetch(`/api/ad-analysis/snapshots/${snapshotId}`, {
            method: 'DELETE',
            credentials: 'same-origin'
        });
        
        const result = await response.json();
        
        if (result.success) {
            alert('✅ 삭제 완료');
            loadSnapshots();
        }
    } catch (error) {
        console.error('Delete error:', error);
        alert('❌ 삭제 실패');
    }
}

// 비교 셀렉트 업데이트
function updateCompareSelects(snapshots) {
    const selectA = document.getElementById('compareSnapshotA');
    const selectB = document.getElementById('compareSnapshotB');
    
    const options = snapshots.map(s => 
        `<option value="${s.id}">${s.snapshot_name} (${s.period_start} ~ ${s.period_end})</option>`
    ).join('');
    
    selectA.innerHTML = '<option value="">선택하세요</option>' + options;
    selectB.innerHTML = '<option value="">선택하세요</option>' + options;
}

// 비교 분석
async function compareAnalysis() {
    const snapshotA = document.getElementById('compareSnapshotA').value;
    const snapshotB = document.getElementById('compareSnapshotB').value;
    
    if (!snapshotA || !snapshotB) {
        alert('두 분석을 모두 선택하세요.');
        return;
    }
    
    try {
        const response = await fetch(`/api/ad-analysis/compare?snapshot_a=${snapshotA}&snapshot_b=${snapshotB}`, {
            credentials: 'same-origin'
        });
        
        const result = await response.json();
        
        // 결과 표시
        document.getElementById('comparisonResult').classList.remove('hidden');
        document.getElementById('comparisonSummary').textContent = result.summary;
        
        const tbody = document.getElementById('comparisonTableBody');
        const comparison = result.comparison;
        
        const labels = {
            'avg_roas': 'ROAS',
            'avg_ctr': 'CTR',
            'avg_cpa': 'CPA',
            'cvr': '전환율',
            'avg_cpc': 'CPC'
        };
        
        tbody.innerHTML = Object.entries(comparison).map(([key, data]) => {
            const trendClass = data.trend === 'up' ? 'trend-up' : (data.trend === 'down' ? 'trend-down' : '');
            const arrow = data.trend === 'up' ? '▲' : (data.trend === 'down' ? '▼' : '=');
            
            return `
                <tr>
                    <td>${labels[key]}</td>
                    <td>${data.a}</td>
                    <td>${data.b}</td>
                    <td class="${trendClass}">${arrow} ${Math.abs(data.change)}%</td>
                </tr>
            `;
        }).join('');
        
    } catch (error) {
        console.error('Compare error:', error);
        alert('❌ 비교 실패');
    }
}

// 목표 저장
async function saveGoal() {
    const yearMonth = document.getElementById('goalMonth').value;
    const budget = document.getElementById('goalBudget').value;
    const targetRoas = document.getElementById('goalRoas').value;
    
    if (!yearMonth || !budget || !targetRoas) {
        alert('모든 필드를 입력하세요.');
        return;
    }
    
    try {
        const response = await fetch('/api/ad-analysis/goals', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'same-origin',
            body: JSON.stringify({
                year_month: yearMonth,
                budget: parseFloat(budget),
                target_roas: parseFloat(targetRoas)
            })
        });
        
        const result = await response.json();
        
        if (result.success) {
            alert('✅ 목표 저장 완료!');
            loadBudgetPacing();
        }
    } catch (error) {
        console.error('Save goal error:', error);
        alert('❌ 저장 실패');
    }
}

// 예산 소진 현황 로드
async function loadBudgetPacing() {
    const yearMonth = document.getElementById('goalMonth').value;
    
    try {
        const response = await fetch(`/api/ad-analysis/budget-pacing?year_month=${yearMonth}`, {
            credentials: 'same-origin'
        });
        
        const data = await response.json();
        
        if (data.error) {
            document.getElementById('budgetPacing').innerHTML = `<p>${data.error}</p>`;
            return;
        }
        
        const statusColor = data.status === 'FAST' ? '#e74c3c' : (data.status === 'SLOW' ? '#f39c12' : '#2ecc71');
        
        document.getElementById('budgetPacing').innerHTML = `
            <div style="padding: 20px; background: #f8f9fa; border-radius: 8px;">
                <h3>월 예산: ${(data.budget / 10000).toLocaleString()}만원</h3>
                <p>사용액: ${(data.spent / 10000).toLocaleString()}만원 (${data.spent_rate}%)</p>
                
                <div style="background: #ecf0f1; height: 30px; border-radius: 15px; overflow: hidden; margin: 15px 0;">
                    <div style="width: ${data.spent_rate}%; height: 100%; background: ${statusColor}; transition: width 0.5s;"></div>
                </div>
                
                <p>진행률: ${data.progress_rate}% (${data.days_passed}/${data.days_total}일)</p>
                <p style="color: ${statusColor}; font-weight: 600; font-size: 18px; margin-top: 10px;">
                    ${data.status === 'FAST' ? '⚠️ 빠름' : (data.status === 'SLOW' ? '⏰ 느림' : '✅ 정상')}
                </p>
                <p>${data.suggestion}</p>
            </div>
        `;
        
    } catch (error) {
        console.error('Load pacing error:', error);
    }
}

// 템플릿 다운로드
function downloadTemplate(type) {
    window.location.href = `/api/ad-analysis/template/${type}`;
}

// PDF 내보내기
function exportPDF() {
    if (!currentSnapshotId) {
        alert('내보낼 분석이 없습니다.');
        return;
    }
    
    window.open(`/api/ad-analysis/export/pdf/${currentSnapshotId}`, '_blank');
}

// Excel 내보내기
function exportExcel() {
    if (!currentSnapshotId) {
        alert('내보낼 분석이 없습니다.');
        return;
    }
    
    window.open(`/api/ad-analysis/export/excel/${currentSnapshotId}`, '_blank');
}

// 수기 입력 모달
function openManualInputModal() {
    manualDataBuffer = [];
    document.getElementById('manualInputModal').style.display = 'block';
    document.getElementById('manualDate').valueAsDate = new Date();
    updateManualDataCount();
}

function closeManualInputModal() {
    document.getElementById('manualInputModal').style.display = 'none';
}

function addManualData() {
    const data = {
        date: document.getElementById('manualDate').value,
        campaign_name: document.getElementById('manualCampaign').value,
        spend: parseFloat(document.getElementById('manualSpend').value),
        clicks: parseInt(document.getElementById('manualClicks').value),
        conversions: parseInt(document.getElementById('manualConversions').value),
        revenue: parseFloat(document.getElementById('manualRevenue').value)
    };
    
    // 유효성 검사
    if (!data.date || !data.campaign_name || !data.spend || !data.clicks || !data.conversions || !data.revenue) {
        alert('모든 필드를 입력하세요.');
        return;
    }
    
    manualDataBuffer.push(data);
    updateManualDataCount();
    
    // 폼 초기화 (날짜와 캠페인명 제외)
    document.getElementById('manualSpend').value = '';
    document.getElementById('manualClicks').value = '';
    document.getElementById('manualConversions').value = '';
    document.getElementById('manualRevenue').value = '';
    
    alert('✅ 데이터 추가됨');
}

function updateManualDataCount() {
    document.getElementById('manualDataCount').textContent = manualDataBuffer.length;
}

async function submitManualData() {
    if (manualDataBuffer.length === 0) {
        alert('입력된 데이터가 없습니다.');
        return;
    }
    
    try {
        const response = await fetch('/api/ad-analysis/manual-input', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'same-origin',
            body: JSON.stringify({
                snapshot_name: `수기입력 ${new Date().toLocaleDateString()}`,
                data: manualDataBuffer
            })
        });
        
        const result = await response.json();
        
        if (result.success) {
            alert('✅ 데이터 저장 완료!');
            closeManualInputModal();
            
            // 자동으로 분석 로드
            loadSnapshot(result.snapshot_id);
        }
    } catch (error) {
        console.error('Submit error:', error);
        alert('❌ 저장 실패');
    }
}
```

---

## 배포 방법

### 1. Flask 앱에 라우트 등록

```python
# main.py 또는 app.py

from routes.ad_analysis import ad_bp

app.register_blueprint(ad_bp)
```

### 2. 환경 변수 설정

```bash
# .env
OPENAI_API_KEY=sk-your-api-key-here
```

### 3. 필요한 패키지 설치

```bash
pip install --break-system-packages pandas openpyxl openai reportlab xlsxwriter
```

### 4. 데이터베이스 마이그레이션

```bash
# SQL 파일 실행
mysql -u username -p database_name < ad_analysis_schema.sql
```

### 5. 정적 파일 준비

- Excel 템플릿 파일을 `/static/templates/` 에 배치
- 템플릿 파일 생성 (ad_template_generic.xlsx 등)

---

## 다음 단계

1. **MVP 구현**: 파일 업로드 + 기본 차트 + 저장 기능
2. **AI 연동**: OpenAI API 연동 및 인사이트 생성
3. **고도화**: 비교 분석, 목표 관리, 예산 페이싱
4. **UI 개선**: 반응형, 애니메이션, 사용자 피드백

---

## 참고사항

- 기존 mbizsquare.com의 세션 관리 로직을 그대로 활용
- MariaDB 연결은 기존 database.py의 `db` 객체 사용
- 사용자 인증은 `session['user_id']`로 확인
- 모든 API는 `/api/ad-analysis/` prefix 사용

이 문서를 Claude Code에 전달하면 바로 구현을 시작할 수 있습니다.