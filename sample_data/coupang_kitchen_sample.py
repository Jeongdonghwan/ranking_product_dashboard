"""
쿠팡 주방용품 샘플 데이터 생성기
- 평균 ROAS 약 1000% (800~1200% 범위)
- 제품 가격 15,000~30,000원
- 총 광고비 약 600만원
"""

import pandas as pd
import numpy as np
from datetime import datetime
import os

# 카테고리별 키워드와 가격 설정
categories = {
    '팬류': {
        'keywords': [
            '후라이팬', '스텐팬', '스테인레스 후라이팬', '인덕션용 후라이팬', '인덕션 프라이팬',
            '코팅 후라이팬', '무쇠 후라이팬', '티타늄 후라이팬', '계란 후라이팬', '미니 후라이팬',
            '대형 후라이팬', '28cm 후라이팬', '세라믹 후라이팬', '논스틱 후라이팬', '그릴팬',
            '궁중팬', '웍', '중화팬', '볶음팬', '스테인리스 프라이팬',
            '26cm 프라이팬', '30cm 후라이팬', '후라이팬 세트', '팬 세트', '인덕션팬',
            '다이아몬드 코팅팬', '마블코팅 후라이팬', '테팔 후라이팬', '휘슬러 팬', '피스카스 팬',
            '생선구이팬', '계란말이팬', '에그팬', '사각팬', '깊은 후라이팬',
            '뚜껑있는 후라이팬', '손잡이 분리 팬', '캠핑팬', '1인용 후라이팬', '업소용 후라이팬',
        ],
        'prices': [19900, 24900, 29900]
    },
    '냄비류': {
        'keywords': [
            '냄비세트', '스텐냄비', '편수냄비', '양수냄비', '냄비 세트',
            '인덕션 냄비', '스테인레스 냄비세트', '압력솥', '전기압력밥솥', '냄비 4종세트',
            '라면냄비', '찜냄비', '전골냄비', '샤브샤브 냄비', '무쇠솥',
            '스톡팟', '국냄비', '이유식냄비', '미니냄비', '대용량 냄비',
            '냄비 3종세트', '냄비 5종세트', '솥밥냄비', '돌솥', '뚝배기',
            '파스타냄비', '찜기', '이중냄비', '멀티냄비', '캠핑냄비',
            '휘슬러 냄비', '피스카스 냄비', 'WMF 냄비', '실리트 냄비', '독일 냄비',
            '무수분 냄비', '저압솥', '전기냄비', '라면포트', '밀크팬',
        ],
        'prices': [22900, 27900]
    },
    '조리도구': {
        'keywords': [
            '조리도구세트', '키친툴세트', '실리콘 조리도구', '실리콘 주걱', '뒤집개',
            '국자', '스테인레스 조리도구', '나무 조리도구', '요리집게', '거품기',
            '감자칼', '필러', '채칼', '강판', '다지기',
            '믹싱볼', '계량컵', '계량스푼', '타이머', '온도계',
            '볼세트', '스텐볼', '믹싱볼세트', '샐러드스피너', '야채탈수기',
            '마늘다지기', '마늘프레스', '양파다지기', '채썰기', '슬라이서',
            '만능채칼', '멀티초퍼', '푸드프로세서', '핸드블렌더', '미니믹서기',
            '절구', '막자사발', '소스볼', '종지', '앞접시',
            '주방저울', '전자저울', '베이킹저울', '실리콘매트', '오븐장갑',
            '실리콘장갑', '앞치마', '주방타월', '행주', '극세사행주',
        ],
        'prices': [15900, 18900]
    },
    '수납정리': {
        'keywords': [
            '식기건조대', '싱크대정리대', '냄비정리대', '주방수납', '냄비뚜껑 정리대',
            '프라이팬 거치대', '싱크대 선반', '조리도구 꽂이', '수저통', '주방 선반',
            '식기 정리대', '그릇 정리대', '컵 정리대', '냉장고 정리함', '주방 바구니',
            '싱크대 매트', '행주걸이', '수세미 거치대', '세제통', '분리수거함',
            '주방 후크', '벽걸이 선반', '자석 칼꽂이', '칼블럭', '칼꽂이',
            '도마 거치대', '냄비받침', '냄비받침대', '실리콘 냄비받침', '스텐 선반',
            '틈새 수납장', '주방 수납장', '양념통 세트', '조미료통', '오일병',
            '주방 정리대', '접시꽂이', '그릇꽂이', '팬정리대', '주방 트레이',
        ],
        'prices': [16900, 19900]
    },
    '식기류': {
        'keywords': [
            '그릇세트', '유리컵', '접시 세트', '밥그릇', '국그릇',
            '머그컵', '텀블러', '물병', '반찬통 세트', '밀폐용기',
            '도자기 그릇', '스테인리스 식기', '아이 식기세트', '커플 식기', '혼수 그릇',
            '샐러드볼', '파스타 접시', '스테이크 접시', '디저트 접시', '브런치 그릇',
            '국그릇세트', '밥공기', '대접', '면기', '덮밥그릇',
            '카레접시', '볶음밥접시', '찬기', '종지세트', '간장종지',
            '유리그릇', '유리볼', '유리접시', '유리밀폐용기', '내열유리용기',
            '도자기접시', '본차이나', '코렐', '루미낙', '이케아식기',
            '스텐식기', '스텐접시', '스텐밥그릇', '캠핑식기', '피크닉식기',
            '아기그릇', '유아식기', '실리콘식기', '빨대컵', '이유식용기',
        ],
        'prices': [17900, 21900]
    },
    '칼도마': {
        'keywords': [
            '도마', '나무도마', '항균도마', '칼세트', '주방칼',
            '과도', '빵칼', '칼갈이', '가위', '주방가위',
            '셰프나이프', '산토쿠칼', '식도', '중식도', '회칼',
            '고기칼', '뼈칼', '채소칼', '과일칼', '껍질칼',
            'TPU도마', '실리콘도마', '대나무도마', '원목도마', '미끄럼방지도마',
            '도마세트', '칼도마세트', '헹켈칼', '글로벌칼', '백종원칼',
        ],
        'prices': [19900, 25900]
    },
    '보관용기': {
        'keywords': [
            '밀폐용기 세트', '유리밀폐용기', '스텐밀폐용기', '플라스틱밀폐용기', '락앤락',
            '반찬통', '김치통', '쌀통', '잡곡통', '시리얼통',
            '냉동실용기', '냉장고정리용기', '소분용기', '이유식용기', '도시락',
            '보온도시락', '스텐도시락', '직장인도시락', '학생도시락', '피크닉도시락',
            '물통', '보온병', '보냉병', '스텐물병', '어린이물병',
            '텀블러세트', '아이스텀블러', '보온텀블러', '커피텀블러', '대용량텀블러',
        ],
        'prices': [15900, 18900]
    },
    '에어프라이어용품': {
        'keywords': [
            '에어프라이어 용품', '전자레인지 용기', '오븐용 그릇', '유리 밀폐용기', '스텐 밀폐용기',
            '에어프라이어종이', '에어프라이어트레이', '에어프라이어악세사리', '실리콘트레이', '베이킹틀',
            '오븐팬', '베이킹팬', '쿠키틀', '케이크틀', '머핀틀',
            '식힘망', '베이킹매트', '유산지', '짤주머니', '스패튤라'
        ],
        'prices': [14900, 17900]
    }
}

# 전체 키워드 리스트 생성 (카테고리 정보 포함)
all_keywords = []
for cat_name, cat_data in categories.items():
    for kw in cat_data['keywords']:
        all_keywords.append({
            'keyword': kw,
            'category': cat_name,
            'prices': cat_data['prices']
        })

num_keywords = len(all_keywords)
print(f"총 키워드 수: {num_keywords}개")

# 총 광고비 설정 (약 600만원)
np.random.seed(2024)
total_ad_spend = 6_200_000

# 키워드별 광고비 분배 (롱테일 분포)
weights = np.random.exponential(1, num_keywords)
weights = weights / weights.sum()
ad_spends = (weights * total_ad_spend).astype(int)
ad_spends[-1] = total_ad_spend - ad_spends[:-1].sum()

# 데이터 생성
data = []

for i, kw_info in enumerate(all_keywords):
    keyword = kw_info['keyword']
    category = kw_info['category']
    prices = kw_info['prices']

    ad_spend = ad_spends[i]

    # 제품 가격 랜덤 선택
    product_price = np.random.choice(prices)

    # CPC (클릭당 비용): 200~500원
    cpc = np.random.randint(200, 500)
    clicks = max(1, ad_spend // cpc)

    # CTR (클릭률): 1~4%
    ctr = np.random.uniform(1.0, 4.0)
    impressions = int(clicks / (ctr / 100))

    # ROAS 분포 설정 (평균 ~1000% 목표, 현실적 분포)
    # 실제 광고에서는 전환 0, 낭비 키워드가 상당수 존재
    rand_val = np.random.random()

    if rand_val < 0.05:  # 5% - 전환 없음 (0%) - 광고비만 소진
        target_roas = 0.0
    elif rand_val < 0.12:  # 7% - 극히 낭비 (1~50%)
        target_roas = np.random.uniform(0.01, 0.5)
    elif rand_val < 0.20:  # 8% - 낭비 (50~150%)
        target_roas = np.random.uniform(0.5, 1.5)
    elif rand_val < 0.32:  # 12% - 손해 (150~350%)
        target_roas = np.random.uniform(1.5, 3.5)
    elif rand_val < 0.47:  # 15% - 저조 (350~600%)
        target_roas = np.random.uniform(3.5, 6.0)
    elif rand_val < 0.62:  # 15% - 보통 (600~900%)
        target_roas = np.random.uniform(6.0, 9.0)
    elif rand_val < 0.77:  # 15% - 양호 (900~1300%)
        target_roas = np.random.uniform(9.0, 13.0)
    elif rand_val < 0.90:  # 13% - 우수 (1300~2200%)
        target_roas = np.random.uniform(13.0, 22.0)
    else:  # 10% - 탁월 (2200~4000%)
        target_roas = np.random.uniform(22.0, 40.0)

    # 목표 매출 계산
    target_revenue = int(ad_spend * target_roas)

    # 주문수 역산
    if target_roas == 0:
        # 전환 0건
        orders = 0
        quantity = 0
        revenue = 0
    else:
        additional_purchase_rate = np.random.uniform(1.1, 1.4)
        orders = max(1, int(target_revenue / (product_price * additional_purchase_rate)))
        quantity = int(orders * additional_purchase_rate)
        revenue = quantity * product_price

    # 실제 ROAS
    actual_roas = round((revenue / ad_spend) * 100, 1) if ad_spend > 0 else 0

    # 전환율 재계산 (주문수 기준)
    actual_cvr = round((orders / clicks * 100), 2) if clicks > 0 else 0

    data.append({
        '키워드': keyword,
        '광고 노출 지면': '검색 영역',
        '노출수': impressions,
        '클릭수': clicks,
        '클릭률': round(ctr, 2),
        '광고비': ad_spend,
        '총 주문수(14일)': orders,
        '총 판매수량(14일)': quantity,
        '총 전환매출액(14일)': revenue,
        '총광고수익률(14일)': actual_roas
    })

# 비검색영역 추가 (전체의 약 12%)
non_search_spend = int(total_ad_spend * 0.12)
non_search_roas = np.random.uniform(7.0, 9.0)  # 비검색은 ROAS 약간 낮음
non_search_revenue = int(non_search_spend * non_search_roas)
data.append({
    '키워드': '-',
    '광고 노출 지면': '비검색영역 (상품상세,장바구니)',
    '노출수': 720000,
    '클릭수': 3500,
    '클릭률': 0.49,
    '광고비': non_search_spend,
    '총 주문수(14일)': int(non_search_revenue / 21900),
    '총 판매수량(14일)': int(non_search_revenue / 21900 * 1.2),
    '총 전환매출액(14일)': non_search_revenue,
    '총광고수익률(14일)': round((non_search_revenue / non_search_spend) * 100, 1)
})

# 리타겟팅 추가 (ROAS 높음)
retarget_spend = int(total_ad_spend * 0.08)
retarget_roas = np.random.uniform(13.0, 16.0)
retarget_revenue = int(retarget_spend * retarget_roas)
data.append({
    '키워드': '-',
    '광고 노출 지면': '리타겟팅',
    '노출수': 280000,
    '클릭수': 2400,
    '클릭률': 0.86,
    '광고비': retarget_spend,
    '총 주문수(14일)': int(retarget_revenue / 24900),
    '총 판매수량(14일)': int(retarget_revenue / 24900 * 1.3),
    '총 전환매출액(14일)': retarget_revenue,
    '총광고수익률(14일)': round((retarget_revenue / retarget_spend) * 100, 1)
})

# DataFrame 생성
df = pd.DataFrame(data)

# 결과 확인
final_spend = df['광고비'].sum()
final_revenue = df['총 전환매출액(14일)'].sum()
final_roas = final_revenue / final_spend

print(f"\n=== 최종 결과 ===")
print(f"총 광고비: {final_spend:,}원")
print(f"총 매출: {final_revenue:,}원")
print(f"평균 ROAS: {final_roas * 100:.1f}%")
print(f"키워드 수: {len(df)}개")

# ROAS 분포 통계 (세분화)
print("\n=== ROAS 분포 ===")
roas_col = df['총광고수익률(14일)']
print(f"전환없음 (0%): {len(df[roas_col == 0])}개")
print(f"극히낭비 (1~100%): {len(df[(roas_col > 0) & (roas_col <= 100)])}개")
print(f"낭비 (100~200%): {len(df[(roas_col > 100) & (roas_col <= 200)])}개")
print(f"손해 (200~400%): {len(df[(roas_col > 200) & (roas_col <= 400)])}개")
print(f"저조 (400~600%): {len(df[(roas_col > 400) & (roas_col <= 600)])}개")
print(f"보통 (600~900%): {len(df[(roas_col > 600) & (roas_col <= 900)])}개")
print(f"양호 (900~1300%): {len(df[(roas_col > 900) & (roas_col <= 1300)])}개")
print(f"우수 (1300~2200%): {len(df[(roas_col > 1300) & (roas_col <= 2200)])}개")
print(f"탁월 (2200%+): {len(df[roas_col > 2200])}개")

# Excel 저장
output_dir = os.path.dirname(os.path.abspath(__file__))
output_path = os.path.join(output_dir, 'coupang_kitchen_sample.xlsx')
df.to_excel(output_path, index=False, engine='openpyxl')
print(f"\n파일 저장: {output_path}")

# 상위 20개 키워드 출력 (광고비 기준)
print("\n=== 상위 20개 키워드 (광고비 기준) ===")
top20 = df.nlargest(20, '광고비')[['키워드', '광고비', '총 전환매출액(14일)', '총광고수익률(14일)']]
print(top20.to_string(index=False))

# 저조 키워드 출력
print("\n=== 저조 키워드 (ROAS 600% 이하) ===")
low_keywords = df[df['총광고수익률(14일)'] <= 600].sort_values('광고비', ascending=False)
low_keywords = low_keywords[['키워드', '광고비', '총 전환매출액(14일)', '총광고수익률(14일)']]
print(low_keywords.head(15).to_string(index=False))
print(f"\n저조 키워드 총 광고비: {low_keywords['광고비'].sum():,}원")

# 우수 키워드 출력
print("\n=== 우수 키워드 (ROAS 1200% 이상) ===")
good_keywords = df[df['총광고수익률(14일)'] >= 1200].sort_values('총광고수익률(14일)', ascending=False)
good_keywords = good_keywords[['키워드', '광고비', '총 전환매출액(14일)', '총광고수익률(14일)']]
print(good_keywords.head(15).to_string(index=False))
