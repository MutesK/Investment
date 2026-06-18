import pandas as pd

df = pd.read_excel('/Users/mute/Documents/Workspace/Investment/2025-06-18~2026-06-18.xlsx', sheet_name='뱅샐현황', engine='openpyxl')
df = df.fillna('')

current_section = None
real_estate = []
accounts = []

for index, row in df.iterrows():
    col1 = str(row.iloc[1]).strip() if len(row) > 1 else ''
    col2 = str(row.iloc[2]).strip() if len(row) > 2 else ''
    
    if '3.자산현황' in col1:
        current_section = '자산'
        continue
    elif '4.보험현황' in col1:
        current_section = '보험'
        continue
    elif '5.투자현황' in col1:
        current_section = '투자'
        continue
    elif '6.대출현황' in col1:
        current_section = '대출'
        continue
        
    if current_section == '자산':
        if col1 == '부동산':
            val_str = str(row.iloc[4]) if len(row) > 4 else '0'
            print("Found 부동산:", col2, val_str)
            try:
                val = float(val_str)
                real_estate.append((col2, val))
            except Exception as e:
                print("Error parsing 부동산", e)
        elif col2 in ['기본계좌', '연금저축', '중개형ISA', '위탁계좌', '종합계좌', '종합위탁']:
            val_str = str(row.iloc[4]) if len(row) > 4 else '0'
            print("Found 계좌:", col2, val_str)
            try:
                val = float(val_str)
                if val > 0:
                    accounts.append((col2, val))
            except Exception as e:
                print("Error parsing 계좌", e)

print("Real Estate:", real_estate)
print("Accounts:", accounts)
