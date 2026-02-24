import pandas as pd
from datetime import datetime

# --- 严格保留：业务性质分类 (从原 app.py 搬运) ---
CORE_BIZ = ["工程收入", "施工收入", "产品销售收入", "服务收入", "预收款", "工程成本", "施工成本", "产品销售支出"]
INC_OTHER = ["期初调整","网络收入", "其他收入", "借款", "往来款收回", "押金收回"]
EXP_OTHER = ["网络成本", "管理费用", "差旅费", "工资福利", "往来款支付", "押金支付", "归还借款"]
ALL_PROPS = CORE_BIZ[:5] + INC_OTHER + CORE_BIZ[5:] + EXP_OTHER + ["资金结转"]

def prepare_new_data(current_df, entry_data, LOCAL_TZ):
    """
    负责：生成编号、计算收支、拼装新行、重算余额
    entry_data: 一个字典，包含从表单收集的所有字段
    """
    now_dt = datetime.now(LOCAL_TZ)
    now_ts = now_dt.strftime("%Y-%m-%d %H:%M")
    today_str = now_dt.strftime("%Y%m%d")

    # --- 1. 编号生成逻辑 (完全保留自原 app.py) ---
    today_mask = current_df['录入编号'].astype(str).str.contains(f"R{today_str}", na=False)
    today_records = current_df[today_mask]
    start_num = (int(str(today_records['录入编号'].iloc[-1])[-3:]) + 1) if not today_records.empty else 1

    # --- 2. 内部函数：创建行模板 (完全保留自原 app.py) ---
    def create_row(offset, s, p, a, i, pr, raw_v, raw_c, inc, exp, h, n):
        sn = f"R{today_str}{(start_num + offset):03d}"
        return [sn, now_ts, now_ts, s, p, a, i, pr, round(float(raw_v), 2), raw_c, 
                round(float(inc), 2), round(float(exp), 2), 0, h, n]

    new_rows = []
    v = entry_data # 字典引用
    
    # --- 3. 构造新行 (完全保留自原 app.py) ---
    if v['is_transfer']:
        new_rows.append(create_row(0, f"【转出】{v['val_sum']}", "内部调拨", v['val_acc_from'], v['val_inv'], v['val_prop'], v['val_amt'], v['val_curr'], 0, v['converted_usd'], v['val_hand'], v['val_note']))
        new_rows.append(create_row(1, f"【转入】{v['val_sum']}", "内部调拨", v['val_acc_to'], v['val_inv'], v['val_prop'], v['val_amt'], v['val_curr'], v['converted_usd'], 0, v['val_hand'], v['val_note']))
    else:
        # 判断收入还是支出
        inc_val = v['converted_usd'] if (v['val_prop'] in CORE_BIZ[:5] or v['val_prop'] in INC_OTHER) else 0
        exp_val = v['converted_usd'] if (v['val_prop'] in CORE_BIZ[5:] or v['val_prop'] in EXP_OTHER) else 0
        new_rows.append(create_row(0, v['val_sum'], v['val_proj'], v['val_acc'], v['val_inv'], v['val_prop'], v['val_amt'], v['val_curr'], inc_val, exp_val, v['val_hand'], v['val_note']))

    # --- 4. 合并并重算余额 (完全保留自原 app.py) ---
    new_df_rows = pd.DataFrame(new_rows, columns=current_df.columns)
    full_df = pd.concat([current_df, new_df_rows], ignore_index=True)
    
    # 数值清理与重算累计余额 (Cumsum)
    for col in ['收入(USD)', '支出(USD)']:
        full_df[col] = pd.to_numeric(full_df[col].astype(str).str.replace(',', ''), errors='coerce').fillna(0)
    
    full_df['余额(USD)'] = full_df['收入(USD)'].cumsum() - full_df['支出(USD)'].cumsum()

    # 格式化输出
    for col in ['收入(USD)', '支出(USD)', '余额(USD)']:
        full_df[col] = full_df[col].apply(lambda x: "{:.2f}".format(float(x)))
        
    return full_df, [r[0] for r in new_rows]

def calculate_full_balance(df):
    """
    辅助函数：当删除或修改后，重新计算整表的余额
    """
    temp_df = df.copy()
    for col in ['收入(USD)', '支出(USD)']:
        temp_df[col] = pd.to_numeric(temp_df[col].astype(str).str.replace(',', ''), errors='coerce').fillna(0)
    
    temp_df['余额(USD)'] = temp_df['收入(USD)'].cumsum() - temp_df['支出(USD)'].cumsum()
    
    for col in ['收入(USD)', '支出(USD)', '余额(USD)']:
        temp_df[col] = temp_df[col].apply(lambda x: "{:.2f}".format(float(x)))
    return temp_df
