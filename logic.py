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

ALL_CURRENCIES = ["USD", "CNY", "KHR", "HKD", "VND", "IDR", "THB"]

CORE_BIZ = ["工程收入", "施工收入", "产品销售收入", "服务收入", "预收款", "工程成本", "施工成本", "产品销售支出"]
INC_OTHER = ["期初调整", "网络收入", "其他收入", "借款", "往来款收回", "押金收回"]
EXP_OTHER = ["网络成本", "管理费用", "差旅费", "工资福利", "往来款支付", "押金支付", "归还借款"]
ALL_PROPS = CORE_BIZ[:5] + INC_OTHER + CORE_BIZ[5:] + EXP_OTHER + ["资金结转"]

def get_dynamic_options():
    return {
        "currencies": ALL_CURRENCIES,
        "properties": ALL_PROPS
    }

# --- 实时汇率 ---
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
    temp_df = df.copy()
    
    # 1. 强制数值列回归“纯数字”格式（float64）
    cols_to_fix = ['实际金额', '收入(USD)', '支出(USD)', '余额(USD)']
    for col in cols_to_fix:
        if col in temp_df.columns:
            # 这一步非常关键：去掉逗号，转成浮点数
            temp_df[col] = pd.to_numeric(
                temp_df[col].astype(str).str.replace(r'[$,\s]', '', regex=True), 
                errors='coerce'
            ).fillna(0.0)
    
    # 2. 全量重算余额（数字运算）
    temp_df['余额(USD)'] = temp_df['收入(USD)'].cumsum() - temp_df['支出(USD)'].cumsum()

    # --- ⚠️ 关键：删除所有强制转字符串的格式化代码 ---
    # 不要执行 temp_df[col].apply(lambda x: "%.2f" % x) 之类的操作！

    # 3. 函数锁：保持 15 列标准表头
    standard_columns = [
        "录入编号", "提交时间", "修改时间", "摘要", "客户/项目信息", "结算账户", 
        "审批/发票单号", "资金性质", "实际金额", "实际币种", 
        "收入(USD)", "支出(USD)", "余额(USD)", "经手人", "备注"
    ]
    temp_df = temp_df[[c for c in standard_columns if c in temp_df.columns]]
        
    return temp_df
# =========================================================
# 3. 企业微信自动化同步逻辑 (新增)
# =========================================================

def sync_wecom_to_sheets(conn):
    """从企业微信抓取审批单并保存到 Google Sheets"""
    # 1. 获取基础配置 (确保你在 Streamlit Secrets 已填好)
    try:
        CORPID = st.secrets["WECOM_CORPID"]
        SECRET = st.secrets["WECOM_SECRET"]
        TEMPLATE_ID = st.secrets["WECOM_TEMPLATE_ID"]
    except Exception:
        return "❌ 请先在 Streamlit 后台配置 Secrets (ID, Secret, TemplateID)"

    # 2. 获取 Access Token
    token_url = f"https://qyapi.weixin.qq.com/cgi-bin/gettoken?corpid={CORPID}&corpsecret={SECRET}"
    try:
        token_res = requests.get(token_url).json()
        token = token_res.get("access_token")
        if not token:
            return f"❌ Token获取失败: {token_res.get('errmsg')}"
    except Exception as e:
        return f"🌐 网络连接异常: {e}"

    # 3. 获取最近 7 天已通过的审批单 (sp_status=2)
    list_url = f"https://qyapi.weixin.qq.com/cgi-bin/oa/getapprovalinfo?access_token={token}"
    import time
    now = int(time.time())
    payload = {
        "starttime": str(now - 604800), 
        "endtime": str(now),
        "cursor": 0,
        "size": 100,
        "filters": [
            {"key": "template_id", "value": TEMPLATE_ID},
            {"key": "sp_status", "value": "2"}
        ]
    }
    
    res_list = requests.post(list_url, json=payload).json()
    sp_nos = res_list.get("sp_no_list", [])
    
    if not sp_nos:
        return "📭 最近 7 天没有发现新通过的审批单。"

    # 4. 读取现有数据用于去重
    df_existing = conn.read(worksheet="Transactions")
    existing_ids = df_existing['录入编号'].astype(str).tolist() if '录入编号' in df_existing.columns else []

    new_rows = []
    detail_url = f"https://qyapi.weixin.qq.com/cgi-bin/oa/getapprovaldetail?access_token={token}"
    
    # 获取实时汇率用于转换
    rates = get_live_rates()

    for sp_no in sp_nos:
        unique_id = f"WE-{sp_no[-8:]}" # 生成企微专属编号
        if unique_id in existing_ids:
            continue
            
        det = requests.post(detail_url, json={"sp_no": sp_no}).json()
        info = det.get("info", {})
        contents = info.get("apply_data", {}).get("contents", [])

        try:
            # 🌟 核心映射逻辑 (请根据你企微表单的顺序调整索引数字)
            raw_amt = float(contents[1]['value']['new_number']) # 假设第二个框是金额
            curr = "USD" # 假设默认是USD，如果是多币种需解析 contents
            
            # 计算美元价值
            inc_usd = 0.0
            exp_usd = raw_amt / rates.get(curr, 1.0) # 假设全是支出
            
            row_data = {
                "录入编号": unique_id,
                "提交时间": datetime.fromtimestamp(info.get("apply_time")).strftime('%Y-%m-%d %H:%M'),
                "修改时间": "",
                "摘要": contents[0]['value']['text'], # 假设第一个框是摘要
                "客户/项目信息": "企微同步",
                "结算账户": "待分类",
                "审批/发票单号": sp_no,
                "资金性质": "企微导入",
                "实际金额": raw_amt,
                "实际币种": curr,
                "收入(USD)": inc_usd,
                "支出(USD)": exp_usd,
                "余额(USD)": 0, # 后面会重算
                "经手人": info.get("applyer", {}).get("name"),
                "备注": "来自企业微信自动化同步"
            }
            new_rows.append(row_data)
        except Exception:
            continue

    # 5. 合并、重算并更新
    if new_rows:
        df_new = pd.DataFrame(new_rows)
        # 合并后使用你现有的 calculate_full_balance 函数重新计算所有余额
        full_df = pd.concat([df_existing, df_new], ignore_index=True)
        final_df = calculate_full_balance(full_df)
        
        conn.update(worksheet="Transactions", data=final_df)
        return f"✅ 成功从企微同步 {len(new_rows)} 条数据！"
    
    return "😴 所有单据已在账目中，无需更新。"
    
