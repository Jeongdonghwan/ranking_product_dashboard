"""
AI 인사이트 생성 서비스
- OpenAI GPT-4 API 연동
- 프롬프트 엔지니어링
- 캐싱 및 오류 처리
"""

import os
import logging
from openai import OpenAI
from flask import current_app

logger = logging.getLogger(__name__)


class AIInsights:
    """AI 인사이트 생성 클래스"""

    def __init__(self):
        """
        OpenAI 클라이언트 초기화
        """
        api_key = current_app.config.get('OPENAI_API_KEY') or os.getenv('OPENAI_API_KEY')

        if not api_key:
            logger.warning("OpenAI API key not configured")
            self.client = None
        else:
            self.client = OpenAI(api_key=api_key)
            logger.info("OpenAI client initialized")

    def generate_insights(self, metrics, df=None):
        """
        AI 인사이트 생성

        Args:
            metrics (dict): 계산된 지표
            df (pd.DataFrame, optional): 원본 데이터프레임

        Returns:
            str: AI 생성 인사이트

        Example:
            insights = ai_insights.generate_insights(metrics, df)
        """
        if not self.client:
            logger.warning("OpenAI client not available, returning fallback insights")
            return self._generate_fallback_insights(metrics)

        try:
            # 프롬프트 생성
            prompt = self._create_prompt(metrics, df)

            # OpenAI API 호출
            response = self.client.chat.completions.create(
                model=current_app.config.get('OPENAI_MODEL', 'gpt-4'),
                messages=[
                    {
                        "role": "system",
                        "content": "당신은 10년 경력의 디지털 마케팅 전문가입니다. 광고 데이터를 분석하고 실행 가능한 조언을 제공합니다."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.7,
                max_tokens=1500
            )

            insights = response.choices[0].message.content

            logger.info("AI insights generated successfully")

            return insights

        except Exception as e:
            logger.error(f"AI insights generation failed: {e}")
            return self._generate_fallback_insights(metrics)

    def _create_prompt(self, metrics, df=None):
        """
        프롬프트 생성

        Args:
            metrics (dict): 계산된 지표
            df (pd.DataFrame, optional): 원본 데이터프레임

        Returns:
            str: 프롬프트 텍스트
        """
        # 캠페인별 ROAS 정리
        campaigns = metrics.get('campaigns', [])
        campaign_text = "\n".join([
            f"- {c['campaign_name']}: ROAS {c['roas']}, 지출 {c['spend']:,.0f}원, CTR {c['ctr']}%, CVR {c['cvr']}%"
            for c in campaigns[:10]  # 상위 10개
        ])

        # 일별 트렌드 요약
        daily = metrics.get('daily_trend', [])
        if len(daily) >= 7:
            recent_roas = [d['roas'] for d in daily[-7:]]
            roas_trend = "상승" if recent_roas[-1] > recent_roas[0] else "하락"
            roas_volatility = "안정적" if max(recent_roas) - min(recent_roas) < 1.0 else "변동성 높음"
        else:
            roas_trend = "데이터 부족"
            roas_volatility = "분석 불가"

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
- 총 전환수: {metrics['total_conversions']:,}

## 캠페인별 성과 (ROAS 순)
{campaign_text if campaign_text else "캠페인 데이터 없음"}

## 최근 7일 트렌드
- ROAS: {roas_trend} 추세
- 변동성: {roas_volatility}

다음 형식으로 작성해주세요:

### 📊 3줄 요약
1. [핵심 성과 또는 문제점]
2. [주요 발견사항]
3. [가장 시급한 조치사항]

### 🔍 주요 발견사항
- **우수 캠페인**: [ROAS 4.0 이상 캠페인 분석]
- **개선 필요**: [ROAS 3.0 미만 캠페인 분석]
- **특이사항**: [비정상적인 패턴이나 주목할 변화]

### 💡 즉시 실행 가능한 액션 (우선순위 순)
1. [높음] [구체적인 액션 아이템 - 어떤 캠페인에 무엇을 얼마나 조정할지]
2. [높음] [구체적인 액션 아이템]
3. [중간] [구체적인 액션 아이템]
4. [중간] [구체적인 액션 아이템]
5. [낮음] [장기적 개선사항]

### 📈 예산 재배분 제안
- [성과가 좋은 캠페인으로 예산 이동 구체적 금액 제시]
- [성과가 나쁜 캠페인 중단 또는 감액 제안]

**중요**:
- 구체적인 수치와 명확한 근거를 포함하세요
- 마케터가 바로 실행할 수 있는 내용이어야 합니다
- 일반론이 아닌 이 데이터에 특화된 조언을 제공하세요
"""

        return prompt

    def _generate_fallback_insights(self, metrics):
        """
        AI API 사용 불가 시 기본 인사이트 생성

        Args:
            metrics (dict): 계산된 지표

        Returns:
            str: 기본 인사이트
        """
        avg_roas = metrics.get('avg_roas', 0)
        avg_ctr = metrics.get('avg_ctr', 0)
        total_spend = metrics.get('total_spend', 0)
        total_revenue = metrics.get('total_revenue', 0)
        campaigns = metrics.get('campaigns', [])

        # ROAS 평가
        if avg_roas >= 4.0:
            roas_assessment = "✅ 우수한 ROAS (4.0 이상)"
        elif avg_roas >= 3.0:
            roas_assessment = "⚠️ 보통 수준의 ROAS (3.0~4.0)"
        else:
            roas_assessment = "🚨 개선 필요한 ROAS (3.0 미만)"

        # CTR 평가
        if avg_ctr >= 2.5:
            ctr_assessment = "✅ 높은 CTR (2.5% 이상)"
        elif avg_ctr >= 1.5:
            ctr_assessment = "⚠️ 보통 수준의 CTR (1.5~2.5%)"
        else:
            ctr_assessment = "🚨 낮은 CTR (1.5% 미만)"

        # 우수/개선 필요 캠페인 분류
        excellent_campaigns = [c for c in campaigns if c.get('roas', 0) >= 4.0]
        poor_campaigns = [c for c in campaigns if c.get('roas', 0) < 3.0]

        insights = f"""### 📊 분석 요약

{roas_assessment}
- 총 지출: {total_spend:,.0f}원
- 총 매출: {total_revenue:,.0f}원
- 평균 ROAS: {avg_roas}

{ctr_assessment}
- 평균 CTR: {avg_ctr}%

### 🔍 주요 발견사항

**우수 캠페인 ({len(excellent_campaigns)}개):**
"""

        if excellent_campaigns:
            for camp in excellent_campaigns[:3]:
                insights += f"\n- {camp['campaign_name']}: ROAS {camp['roas']}"
        else:
            insights += "\n- 없음 (ROAS 4.0 이상 캠페인 없음)"

        insights += f"\n\n**개선 필요 캠페인 ({len(poor_campaigns)}개):**\n"

        if poor_campaigns:
            for camp in poor_campaigns[:3]:
                insights += f"\n- {camp['campaign_name']}: ROAS {camp['roas']}"
        else:
            insights += "\n- 없음"

        insights += """

### 💡 권장 조치사항

"""

        if avg_roas < 3.0:
            insights += "1. [높음] 전반적인 ROAS가 낮습니다. 전환율이 낮은 캠페인을 중단하거나 예산을 감축하세요.\n"
        else:
            insights += "1. [중간] 현재 ROAS는 양호합니다. 우수 캠페인에 예산을 추가 배분하는 것을 고려하세요.\n"

        if avg_ctr < 1.5:
            insights += "2. [높음] CTR이 낮습니다. 광고 소재와 타겟팅을 개선하세요.\n"

        if poor_campaigns:
            insights += f"3. [높음] 성과가 낮은 {len(poor_campaigns)}개 캠페인을 검토하고 개선하세요.\n"

        if excellent_campaigns:
            insights += f"4. [중간] 우수 캠페인 {len(excellent_campaigns)}개에 예산을 추가 배분하세요.\n"

        insights += """
5. [낮음] A/B 테스트를 통해 지속적으로 개선하세요.

### 📈 예산 재배분 제안
"""

        if excellent_campaigns and poor_campaigns:
            insights += f"\n- 성과가 낮은 캠페인의 예산 20%를 우수 캠페인으로 이동"
        else:
            insights += "\n- 현재 데이터로는 명확한 재배분 제안이 어렵습니다."

        insights += "\n\n**참고**: 이 인사이트는 기본 분석입니다. AI 기반 인사이트를 사용하려면 OpenAI API 키를 설정하세요."

        return insights

    def generate_comparison_insights(self, comparison):
        """
        기간 비교 인사이트 생성

        Args:
            comparison (dict): 비교 결과

        Returns:
            str: 비교 인사이트
        """
        if not self.client:
            return self._generate_fallback_comparison_insights(comparison)

        try:
            prompt = self._create_comparison_prompt(comparison)

            response = self.client.chat.completions.create(
                model=current_app.config.get('OPENAI_MODEL', 'gpt-4'),
                messages=[
                    {
                        "role": "system",
                        "content": "당신은 광고 성과 분석 전문가입니다. 두 기간의 성과를 비교하고 개선/악화 원인을 분석합니다."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.7,
                max_tokens=800
            )

            insights = response.choices[0].message.content

            logger.info("Comparison insights generated successfully")

            return insights

        except Exception as e:
            logger.error(f"Comparison insights generation failed: {e}")
            return self._generate_fallback_comparison_insights(comparison)

    def _create_comparison_prompt(self, comparison):
        """비교 분석 프롬프트 생성"""
        comp_data = comparison.get('comparison', {})

        prompt = f"""
두 기간의 광고 성과를 비교 분석해주세요:

## 지표 변화
- ROAS: {comp_data.get('avg_roas', {}).get('a')} → {comp_data.get('avg_roas', {}).get('b')} ({comp_data.get('avg_roas', {}).get('change')}% 변화)
- CTR: {comp_data.get('avg_ctr', {}).get('a')}% → {comp_data.get('avg_ctr', {}).get('b')}% ({comp_data.get('avg_ctr', {}).get('change')}% 변화)
- CPA: {comp_data.get('avg_cpa', {}).get('a')}원 → {comp_data.get('avg_cpa', {}).get('b')}원 ({comp_data.get('avg_cpa', {}).get('change')}% 변화)

다음 형식으로 간결하게 작성하세요:

### 📈 개선 사항
[개선된 지표와 원인 분석]

### 📉 악화 사항
[악화된 지표와 원인 분석]

### 💡 권장 조치
1. [구체적인 개선 방안]
2. [구체적인 개선 방안]
"""

        return prompt

    def _generate_fallback_comparison_insights(self, comparison):
        """기본 비교 인사이트"""
        summary = comparison.get('summary', '변화 없음')

        return f"""### 기간 비교 분석

{summary}

**참고**: AI 기반 상세 분석을 사용하려면 OpenAI API 키를 설정하세요.
"""
