import pandas as pd

df = pd.read_excel('/Users/mute/Documents/Workspace/Investment/2025-06-18~2026-06-18.xlsx', sheet_name='뱅샐현황', engine='openpyxl')
df = df.fillna('')

current_section = None

for index, row in df.iterrows():
    col1 = str(row.iloc[1]).strip() if len(row) > 1 else ''
    col2 = str(row.iloc[2]).strip() if len(row) > 2 else ''
    
    if '3.자산현황' in col1:
        current_section = '자산'
        continue
    elif '4.보험현황' in col1:
        current_section = '보험'
        break
        
    if current_section == '자산':
        print(f"Row {index}: col1='{col1}', col2='{col2}'")
