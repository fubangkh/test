import pandas as pd
from datetime import datetime
import time

# 假设你使用的是 st.connection("gsheets", ...)
def calculate_balance(df):
    """专门处理数值转换和余额累加"""
    # 确保数值列没有逗号且为数字类型
    for col in ['收入(USD)', '支出(USD)']:
        df[col] = pd.to_numeric(df[col].astype(str).str.replace(',', ''), errors='coerce').fillna(0)
    
    # 重新计算累计余额
    df['余额(USD)'] = df['收入(USD)'].cumsum() - df['支出(USD)'].cumsum()
    
    # 格式化回字符串（保留两位小数）供存入使用
    for col in ['收入(USD)', '支出(USD)', '余额(USD)']:
        df[col] = df[col].apply(lambda x: "{:.2f}".format(float(x)))
    return df

def generate_sn(current_df, today_str):
    """生成流水编号 R20231027001"""
    today_mask = current_df['录入编号'].astype(str).str.contains(f"R{today_str}", na=False)
    today_records = current_df[today_mask]
    if not today_records.empty:
        last_sn = str(today_records['录入编号'].iloc[-1])
        new_num = int(last_sn[-3:]) + 1
    else:
        new_num = 1
    return f"R{today_str}{new_num:03d}"
