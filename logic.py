import pandas as pd
from datetime import datetime
import requests  # ✨ 必须加上这个，否则 get_live_rates 会报错
import streamlit as st # ✨ 必须加上这个，否则 @st.cache_data 会报错

# =========================================================
# 1. 核心业务常量 (新增币种定义)
# =========================================================

# 统一币种转换字典
ISO_MAP = {
    "人民币": "CNY", "CNY": "CNY", 
    "港币": "HKD", "HKD": "HKD", 
    "印尼盾": "IDR", "IDR": "IDR", 
    "越南盾": "VND", "VND": "VND", 
    "瑞尔": "KHR", "KHR": "KHR", 
    "泰铢": "THB", "THB": "THB", 
    "美元": "USD", "USD": "USD"
}

# --- 必须完全顶格 ---
ALL_CURRENCIES = ["USD", "CNY", "KHR", "HKD", "VND", "IDR", "THB"]

CORE_BIZ = ["工程收入", "施工收入", "产品销售收入", "服务收入", "预收款", "工程成本", "施工成本", "产品销售支出"]
INC_OTHER = ["期初调整", "网络收入", "其他收入", "借款", "往来款收回", "押金收回"]
EXP_OTHER = ["网络成本", "管理费用", "差旅费", "工资福利", "往来款支付", "押金支付", "归还借款"]
ALL_PROPS = CORE_BIZ[:5] + INC_OTHER + CORE_BIZ[5:] + EXP_OTHER + ["资金结转"]

def get_dynamic_options():
    # --- 必须向右缩进 ---
    return {
        "currencies": ALL_CURRENCIES,
        "properties": ALL_PROPS
    }

# --- 实时汇率 (已修复版) ---
@st.cache_data(ttl=3600)
def get_live_rates():
    # 1. 预设完整的币种模板和默认汇率
    final_rates = {
        "USD": 1.0, 
        "CNY": 6.88, 
        "KHR": 4015,
        "VND": 25750, 
        "HKD": 7.82, 
        "IDR": 15600,
        "THB": 31.14
    }
    
    try:
        # 2. 尝试获取 API 实时数据
        response = requests.get("https://open.er-api.com/v6/latest/USD", timeout=5)
        if response.status_code == 200:
            api_data = response.json().get("rates", {})
            
            # 3. 只有当 API 返回的数据里有我们要的币种，才更新 final_rates
            # API 里没有的币种（比如它漏给了 HKD），会保持上面 7.82 的默认值
            for curr in final_rates.keys():
                if curr in api_data:
                    val = api_data[curr]
                    if isinstance(val, (int, float)) and val > 0:
                        final_rates[curr] = float(val)
            
            # 4. 重点：更新完后直接返回这个完整的字典
            return final_rates
            
    except Exception as e:
        print(f"⚠️ API请求异常，已自动切换至本地保底汇率: {e}")
    
    # 5. 重点：如果 API 请求失败（网络不通），依然返回上面那组保底数据
    # 这样 forms.py 拿到的 HKD 至少是 7.82，绝对不会是 1.0
    return final_rates
    
# =========================================================
# 2. 数据处理核心函数
# =========================================================

def prepare_new_data(current_df, v, LOCAL_TZ):
    """
    负责：生成编号、计算收支、拼装新行、重算余额
    v: 传入的 entry_data 字典
    """
    now_dt = datetime.now(LOCAL_TZ)
    now_ts = now_dt.strftime("%Y-%m-%d %H:%M")
    today_str = now_dt.strftime("%Y%m%d")

    # --- A. 编号生成逻辑 ---
    today_mask = current_df['录入编号'].astype(str).str.contains(f"R{today_str}", na=False)
    today_records = current_df[today_mask]
    start_num = (int(str(today_records['录入编号'].iloc[-1])[-3:]) + 1) if not today_records.empty else 1

    # --- B. 内部函数：创建行模板 ---
    def create_row(offset, s, p, a, i, pr, raw_v, raw_c, inc, exp, h, n):
        sn = f"R{today_str}{(start_num + offset):03d}"
        return [sn, now_ts, "", s, p, a, i, pr, round(float(raw_v), 2), raw_c, 
                round(float(inc), 2), round(float(exp), 2), 0, h, n]

    new_rows = []
    
    # --- C. 构造新行 (双分录逻辑) ---
    if v['is_transfer']:
        new_rows.append(create_row(0, f"【转出】{v['sum']}", "内部调拨", v['acc_from'], v['inv'], v['prop'], v['amt'], v['curr'], 0, v['conv_usd'], v['hand'], v['note']))
        new_rows.append(create_row(1, f"【转入】{v['sum']}", "内部調拨", v['acc_to'], v['inv'], v['prop'], v['amt'], v['curr'], v['conv_usd'], 0, v['hand'], v['note']))
    else:
        new_rows.append(create_row(0, v['sum'], v['proj'], v['acc'], v['inv'], v['prop'], v['amt'], v['curr'], v['inc_val'], v['exp_val'], v['hand'], v['note']))

    # --- D. 合并与重算余额 ---
    new_df_rows = pd.DataFrame(new_rows, columns=current_df.columns)
    full_df = pd.concat([current_df, new_df_rows], ignore_index=True)
    
    return calculate_full_balance(full_df), [r[0] for r in new_rows]

def calculate_full_balance(df):
    """
    核心计算逻辑：重算整表的收支数值和累计余额
    """
    temp_df = df.copy()
    
    # 确保数值列干净
    for col in ['收入(USD)', '支出(USD)']:
        if col in temp_df.columns:
            temp_df[col] = pd.to_numeric(temp_df[col].astype(str).str.replace(',', ''), errors='coerce').fillna(0)
    
    # 重新计算余额
    temp_df['余额(USD)'] = temp_df['收入(USD)'].cumsum() - temp_df['支出(USD)'].cumsum()

    # 格式化输出为两位小数
    for col in ['收入(USD)', '支出(USD)', '余额(USD)']:
        if col in temp_df.columns:
            temp_df[col] = temp_df[col].apply(lambda x: "{:.2f}".format(float(x)))
        
    # 函数锁：物理隔离多余列
    standard_columns = [
        "录入编号", "提交时间", "修改时间", "摘要", "客户/项目信息", "结算账户", 
        "审批/发票单号", "资金性质", "实际金额", "实际币种", 
        "收入(USD)", "支出(USD)", "余额(USD)", "经手人", "备注"
    ]
    # 过滤掉不在标准列表里的列（比如 _calc_date）
    temp_df = temp_df[[c for c in standard_columns if c in temp_df.columns]]
        
    return temp_df
