import pandas as pd
from datetime import datetime

# =========================================================
# 1. 核心业务常量 (严格保留原版顺序与切片逻辑)
# =========================================================
CORE_BIZ = ["工程收入", "施工收入", "产品销售收入", "服务收入", "预收款", "工程成本", "施工成本", "产品销售支出"]
INC_OTHER = ["期初调整", "网络收入", "其他收入", "借款", "往来款收回", "押金收回"]
EXP_OTHER = ["网络成本", "管理费用", "差旅费", "工资福利", "往来款支付", "押金支付", "归还借款"]

# 这一行是下拉菜单的排序核心，绝对不能删减
ALL_PROPS = CORE_BIZ[:5] + INC_OTHER + CORE_BIZ[5:] + EXP_OTHER + ["资金结转"]

# =========================================================
# 2. 数据处理核心函数
# =========================================================

def prepare_new_data(current_df, v, LOCAL_TZ):
    """
    负责：生成编号、计算收支、拼装新行、重算余额
    v: 传入的 entry_data 字典，包含从 forms.py 收集的所有字段
    """
    now_dt = datetime.now(LOCAL_TZ)
    now_ts = now_dt.strftime("%Y-%m-%d %H:%M")
    today_str = now_dt.strftime("%Y%m%d")

    # --- A. 编号生成逻辑 (完全保留自原 app.py) ---
    today_mask = current_df['录入编号'].astype(str).str.contains(f"R{today_str}", na=False)
    today_records = current_df[today_mask]
    start_num = (int(str(today_records['录入编号'].iloc[-1])[-3:]) + 1) if not today_records.empty else 1

    # --- B. 内部函数：创建行模板 (完全保留自原 app.py) ---
    def create_row(offset, s, p, a, i, pr, raw_v, raw_c, inc, exp, h, n):
        sn = f"R{today_str}{(start_num + offset):03d}"
        return [sn, now_ts, now_ts, s, p, a, i, pr, round(float(raw_v), 2), raw_c, 
                round(float(inc), 2), round(float(exp), 2), 0, h, n]

    new_rows = []
    
    # --- C. 构造新行 (完全保留自原 app.py 的双分录逻辑) ---
    if v['is_transfer']:
        # 资金结转模式：生成两行记录（一出一入）
        new_rows.append(create_row(0, f"【转出】{v['sum']}", "内部调拨", v['acc_from'], v['inv'], v['prop'], v['amt'], v['curr'], 0, v['conv_usd'], v['hand'], v['note']))
        new_rows.append(create_row(1, f"【转入】{v['sum']}", "内部调拨", v['acc_to'], v['inv'], v['prop'], v['amt'], v['curr'], v['conv_usd'], 0, v['hand'], v['note']))
    else:
        # 常规录入模式
        new_rows.append(create_row(0, v['sum'], v['proj'], v['acc'], v['inv'], v['prop'], v['amt'], v['curr'], v['inc_val'], v['exp_val'], v['hand'], v['note']))

    # --- D. 合并与重算余额 (完全保留自原 app.py) ---
    new_df_rows = pd.DataFrame(new_rows, columns=current_df.columns)
    full_df = pd.concat([current_df, new_df_rows], ignore_index=True)
    
    return calculate_full_balance(full_df), [r[0] for r in new_rows]

def calculate_full_balance(df):
    """
    核心计算逻辑：全量重算整表的收支数值和累计余额
    """
    temp_df = df.copy()
    
    # 1. 清理数值列，确保没有逗号且为数字类型
    for col in ['收入(USD)', '支出(USD)']:
        temp_df[col] = pd.to_numeric(temp_df[col].astype(str).str.replace(',', ''), errors='coerce').fillna(0)
    
    # 2. 关键：全量 Cumsum 重新生成余额链
    temp_df['余额(USD)'] = temp_df['收入(USD)'].cumsum() - temp_df['支出(USD)'].cumsum()

    # 3. 最终格式化为 2 位小数的字符串，确保写入数据库的一致性
    for col in ['收入(USD)', '支出(USD)', '余额(USD)']:
        temp_df[col] = temp_df[col].apply(lambda x: "{:.2f}".format(float(x)))
        
    return temp_df
