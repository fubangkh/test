import pandas as pd
from datetime import datetime

def prepare_new_data(current_df, entry_data, LOCAL_TZ):
    """
    负责：生成编号、计算收支、拼装新行、重算余额
    entry_data: 一个字典，包含从表单收集的 val_sum, val_amt 等
    """
    now_dt = datetime.now(LOCAL_TZ)
    now_ts = now_dt.strftime("%Y-%m-%d %H:%M")
    today_str = now_dt.strftime("%Y%m%d")

    # 1. 生成录入编号
    today_mask = current_df['录入编号'].astype(str).str.contains(f"R{today_str}", na=False)
    today_records = current_df[today_mask]
    start_num = (int(str(today_records['录入编号'].iloc[-1])[-3:]) + 1) if not today_records.empty else 1

    # 2. 内部函数：创建行模板
    def create_row(offset, s, p, a, i, pr, raw_v, raw_c, inc, exp, h, n):
        sn = f"R{today_str}{(start_num + offset):03d}"
        return [sn, now_ts, now_ts, s, p, a, i, pr, round(float(raw_v), 2), raw_c, 
                round(float(inc), 2), round(float(exp), 2), 0, h, n]

    new_rows = []
    v = entry_data # 简化引用
    
    # 3. 判断是结转还是常规收支
    if v['is_transfer']:
        new_rows.append(create_row(0, f"【转出】{v['sum']}", "内部调拨", v['acc_from'], v['inv'], v['prop'], v['amt'], v['curr'], 0, v['conv_usd'], v['hand'], v['note']))
        new_rows.append(create_row(1, f"【转入】{v['sum']}", "内部调拨", v['acc_to'], v['inv'], v['prop'], v['amt'], v['curr'], v['conv_usd'], 0, v['hand'], v['note']))
    else:
        new_rows.append(create_row(0, v['sum'], v['proj'], v['acc'], v['inv'], v['prop'], v['amt'], v['curr'], v['inc_val'], v['exp_val'], v['hand'], v['note']))

    # 4. 合并并重算余额
    new_df_rows = pd.DataFrame(new_rows, columns=current_df.columns)
    full_df = pd.concat([current_df, new_df_rows], ignore_index=True)
    
    # 数值清理与重算累计余额 (Cumsum)
    for col in ['收入(USD)', '支出(USD)']:
        full_df[col] = pd.to_numeric(full_df[col].astype(str).str.replace(',', ''), errors='coerce').fillna(0)
    
    full_df['余额(USD)'] = full_df['收入(USD)'].cumsum() - full_df['支出(USD)'].cumsum()

    # 格式化
    for col in ['收入(USD)', '支出(USD)', '余额(USD)']:
        full_df[col] = full_df[col].apply(lambda x: "{:.2f}".format(float(x)))
        
    return full_df, [r[0] for r in new_rows] # 返回新表和新生成的ID用于确认
