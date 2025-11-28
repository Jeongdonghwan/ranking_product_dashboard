import pandas as pd
import sys

sys.stdout.reconfigure(encoding='utf-8')

df = pd.read_excel('골덴바지(자동광고).xlsx')

nonsearch = df[df['광고 노출 지면'].str.contains('비검색', na=False)]
search = df[df['광고 노출 지면'] == '검색 영역']
retarget = df[df['광고 노출 지면'].str.contains('리타겟팅', na=False)]

print('=== 전체 데이터 ===')
print(f"광고비: {df['광고비'].sum():,.0f}원")
print(f"매출: {df['총 전환매출액(1일)'].sum():,.0f}원")

print('\n=== 비검색영역 (제외 대상) ===')
print(f"Count: {len(nonsearch)}행")
print(f"광고비: {nonsearch['광고비'].sum():,.0f}원")
print(f"매출: {nonsearch['총 전환매출액(1일)'].sum():,.0f}원")

print('\n=== 검색영역 (분석 대상) ===')
print(f"Count: {len(search)}행")
print(f"광고비: {search['광고비'].sum():,.0f}원")
print(f"매출: {search['총 전환매출액(1일)'].sum():,.0f}원")
if search['광고비'].sum() > 0:
    roas = (search['총 전환매출액(1일)'].sum() / search['광고비'].sum() * 100)
    print(f"ROAS: {roas:.2f}%")

print('\n=== 리타겟팅 ===')
print(f"Count: {len(retarget)}행")
print(f"광고비: {retarget['광고비'].sum():,.0f}원")
print(f"매출: {retarget['총 전환매출액(1일)'].sum():,.0f}원")

print('\n=== 검색영역에서 키워드 있는 행만 ===')
search_with_kw = search[search['키워드'] != '-']
print(f"키워드 있는 행: {len(search_with_kw)}개")
print(f"광고비: {search_with_kw['광고비'].sum():,.0f}원")
print(f"매출: {search_with_kw['총 전환매출액(1일)'].sum():,.0f}원")
if search_with_kw['광고비'].sum() > 0:
    roas = (search_with_kw['총 전환매출액(1일)'].sum() / search_with_kw['광고비'].sum() * 100)
    print(f"ROAS: {roas:.2f}%")

# 저성과 키워드 분석
print('\n=== 저성과 키워드 (ROAS 100% 이하) ===')
low_performers = search_with_kw.copy()
low_performers['ROAS'] = (low_performers['총 전환매출액(1일)'] / low_performers['광고비'] * 100).fillna(0)
low_performers = low_performers[low_performers['ROAS'] <= 100]
print(f"Count: {len(low_performers)}개")
print(f"광고비: {low_performers['광고비'].sum():,.0f}원")
print(f"매출: {low_performers['총 전환매출액(1일)'].sum():,.0f}원")

# 광고비 대비 전환 없는 키워드
print('\n=== 전환 없는 키워드 ===')
no_conversion = search_with_kw[search_with_kw['총 전환매출액(1일)'] == 0]
print(f"Count: {len(no_conversion)}개")
print(f"낭비 광고비: {no_conversion['광고비'].sum():,.0f}원")
