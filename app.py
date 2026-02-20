import streamlit as st
import pandas as pd
import time
import pytz
import requests
from datetime import datetime
from streamlit_gsheets import GSheetsConnection

# --- 1. 全局配置 (必须放在最前面) ---
st.set_page_config(page_title="富邦日记账", layout="wide")
LOCAL_TZ = pytz.timezone('Asia/Phnom_Penh')

# --- 2. 登录拦截 ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if not st.session_state.logged_in:
    from login import show_login_page
    show_login_page()
    st.stop()

# --- 3. 登录成功后的主程序逻辑 ---

# A. 整合后的 CSS：包含导航条样式、按钮样式、以及白卡片样式
st.markdown("""
    <style>
    /* 1. 全局背景与隐藏原生页眉 */
    .stApp { background-color: #f8fafc !important; }
    header { visibility: hidden; }
    
    /* 2. 顶部导航条：精简、对齐、适配手机 */
    .nav-container {
        display: flex; 
        align-items: center;
        padding: 12px 18px; 
        background: white;
        border: 1px solid #e2e8f0; 
        border-radius: 16px;       
        margin-bottom: 1.2rem;     
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.02);
    }
    .nav-logo { display: flex; align-items: center; gap: 12px; }
    .logo-sq {
        background: #1f7a3f; color: white; width: 32px; height: 32px;
        border-radius: 8px; display: flex; align-items: center; justify-content: center;
        font-weight: bold; font-size: 14px;
    }

    /* 3. 按钮样式升级 (Primary & Secondary) */
    div.stButton > button[kind="primary"] {
        background-color: #1F883D !important;
        color: white !important;
        border-radius: 12px !important;
        border: none !important;
        transition: all 0.3s ease;
    }
    div.stButton > button[kind="primary"]:hover {
        background-color: #66BB6A !important;
        box-shadow: 0 4px 8px rgba(0,0,0,0.1) !important;
    }
    div.stButton > button[kind="secondary"] {
        border-radius: 12px !important;
        background-color: white !important;
    }

    /* 4. 强制卡片容器风格 (针对 st.container border=True) */
    div[data-testid="stVerticalBlockBorderWrapper"] {
        background-color: white !important;
        border: 1px solid #e2e8f0 !important;
        border-radius: 16px !important;
        box-shadow: 0 2px 4px rgba(0,0,0,0.02) !important;
    }
    </style>
""", unsafe_allow_html=True)

# B. 渲染导航栏
with st.container():
    st.markdown(f"""
        <div class="nav-container">
            <div class="nav-logo">
                <div class="logo-sq">FB</div>
                <div style="font-size: 1.15rem; font-weight: 800; color: #1f7a3f; letter-spacing: 0.5px;">
                    富邦日记账管理系统
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)

# --- 2. 核心功能：实时汇率 ---
@st.cache_data(ttl=3600)
def get_live_rates():
    default_rates = {"USD": 1.0, "RMB": 6.91, "VND": 26000.0, "HKD": 7.82, "IDR": 16848.0}
    try:
        response = requests.get("https://open.er-api.com/v6/latest/USD", timeout=5)
        if response.status_code == 200:
            rates = response.json().get("rates", {})
            return {"USD": 1.0, "RMB": rates.get("CNY", 6.91), "VND": rates.get("VND", 26000), "HKD": rates.get("HKD", 7.82), "IDR": rates.get("IDR", 16848.0)}
    except: pass
    return default_rates

# --- 3. 数据连接 ---
conn = st.connection("gsheets", type=GSheetsConnection)

@st.cache_data(ttl=0)
def load_data():
    # 先读取数据并去掉全空行
    df = conn.read(worksheet="Summary", ttl=0).dropna(how="all")
    # --- 关键新增：把所有的空值 (NaN) 替换成干净的空字符串 ---
    df = df.fillna("")
    return df

def get_dynamic_options(df, column_name):
    try:
        if not df.empty and column_name in df.columns:
            raw_list = [str(x).strip() for x in df[column_name].unique() if x]
            clean_options = sorted([
                x for x in raw_list 
                if x and x not in ["--", "-", "nan", "None", "0", "0.0"] and "➕" not in x
            ])
            # 核心改动：把 "-- 请选择 --" 放在最前面
            return ["-- 请选择 --"] + clean_options + ["➕ 新增..."]
    except:
        pass
    return ["-- 请选择 --", "➕ 新增..."]
    
   # --- 4. 录入弹窗 (针对 13 列结构及报错彻底修复) ---
@st.dialog("📝 新增录入", width="large")
def entry_dialog():
    # --- A. 内部常量定义 ---
    CORE_BIZ = ["工程收入", "施工收入", "产品销售收入", "服务收入", "预收款", "工程成本", "施工成本"]
    INC_OTHER = ["网络收入", "其他收入", "借款", "往来款收回", "押金收回"]
    EXP_OTHER = ["网络成本", "管理费用", "差旅费", "工资福利", "往来款支付", "押金支付", "归还借款"]
    ALL_PROPS = CORE_BIZ[:5] + INC_OTHER + CORE_BIZ[5:] + EXP_OTHER + ["资金结转"]

    df = load_data()
    live_rates = get_live_rates()
    
    # 顶部结余显示
    current_balance = df['余额'].iloc[-1] if not df.empty else 0
    st.write(f"💡 当前总结余: **${current_balance:,.2f}**")
    
    # 1. 摘要与时间
    c1, c2 = st.columns(2)
    val_sum = c1.text_input("摘要内容", placeholder="请输入流水说明")
    val_time = c2.datetime_input("业务时间", value=datetime.now(LOCAL_TZ))
    
    # 2. 金额、币种、汇率
    r2_c1, r2_c2, r2_c3 = st.columns(3)
    val_amt = r2_c1.number_input("实际金额", min_value=0.0, step=100.0)
    val_curr = r2_c2.selectbox("实际币种", list(live_rates.keys()))
    val_rate = r2_c3.number_input("实时汇率", value=float(live_rates[val_curr]), format="%.4f")
    
    # 实时换算显示
    converted_usd = round(val_amt / val_rate, 2) if val_rate != 0 else 0
    st.info(f"💰 换算后金额：$ {converted_usd:,.2f} USD")
    
    st.divider() 

    # 3. 性质与发票
    r4_c1, r4_c2 = st.columns(2)
    val_inv = r4_c1.text_input("📑 审批/发票单号 (必填)")
    val_prop = r4_c2.selectbox("资金性质", ALL_PROPS)
    
    is_transfer = (val_prop == "资金结转")
    is_req = val_prop in CORE_BIZ

    # 4. 账户与经手人
    r3_c1, r3_c2 = st.columns(2)
    if is_transfer:
        val_acc_from = r3_c1.selectbox("➡️ 转出账户", options=get_dynamic_options(df, "结算账户"))
        val_acc_to = r3_c2.selectbox("⬅️ 转入账户", options=get_dynamic_options(df, "结算账户"))
        val_hand = "系统自动结转"
    else:
        sel_acc = r3_c1.selectbox("结算账户", options=get_dynamic_options(df, "结算账户"))
        val_acc = st.text_input("✍️ 录入新账户") if sel_acc == "➕ 新增..." else sel_acc
        sel_hand = r3_c2.selectbox("经手人", options=get_dynamic_options(df, "经手人"))
        val_hand = st.text_input("✍️ 录入新姓名") if sel_hand == "➕ 新增..." else sel_hand

    # --- 5. 项目与备注
    proj_label = "📍 客户/项目信息 (必填)" if is_req else "客户/项目信息 (选填)"
    # 现在 sel_proj 默认会是 "-- 请选择 --"
    sel_proj = st.selectbox(proj_label, options=get_dynamic_options(df, "客户/项目信息"))

    # 如果选了新增，或者还没选（刚打开弹窗时），显示输入框
    if sel_proj == "➕ 新增..." or sel_proj == "-- 请选择 --":
        val_proj = st.text_input("✍️ 录入新客户/项目", value="", key="k_new_proj_input", placeholder="请输入或选择项目名称...")
    else:
        val_proj = sel_proj
    val_note = st.text_area("备注详情")
    
    st.divider()

    # --- 6. 核心提交逻辑函数 (注意这个函数的缩进) ---
    def validate_and_submit():
        if not val_sum.strip():
            st.error("⚠️ 请填写摘要内容！")
            return False
        if val_amt <= 0:
            st.error("⚠️ 金额必须大于 0！")
            return False
        if not val_inv or val_inv.strip() == "":
            st.error("⚠️ 请输入【审批/发票单号】！")
            return False
        if is_req and (not val_proj or val_proj.strip() in ["", "-- 请选择 --", "--", "-"]):
            st.error(f"⚠️ 【{val_prop}】必须关联有效项目！")
            return False
        if is_transfer:
            if val_acc_from == "-- 请选择 --" or val_acc_to == "-- 请选择 --":
                st.error("⚠️ 请选择转出或转入账户！")
                return False
        else:
            if not val_acc or val_acc.strip() in ["", "-- 请选择 --"]:
                st.error("⚠️ 请输入或选择【结算账户】！")
                return False
            if not val_hand or val_hand.strip() in ["", "-- 请选择 --"]:
                st.error("⚠️ 请输入或选择【经手人】！")
                return False
        
        try:
            current_df = load_data()
            now_dt = datetime.now(LOCAL_TZ)
            now_ts = now_dt.strftime("%Y-%m-%d %H:%M:%S")
            today_str = now_dt.strftime("%Y%m%d")

            # 编号生成逻辑 (R + 年月日 + 3位顺位码)
            today_mask = current_df['录入编号'].astype(str).str.contains(f"R{today_str}", na=False)
            today_records = current_df[today_mask]
            start_num = (int(str(today_records['录入编号'].iloc[-1])[-3:]) + 1) if not today_records.empty else 1

            new_rows = []
            # --- 核心修改：定义 15 列结构的行生成函数 ---
            def create_row(offset, s, p, a, i, pr, raw_v, raw_c, inc, exp, h, n):
                sn = f"R{today_str}{(start_num + offset):03d}"
                # 严格对应 Sheets 15列顺序：
                # 1.录入编号, 2.提交时间, 3.修改时间, 4.摘要, 5.客户/项目信息, 6.结算账户, 
                # 7.审批/发票单号, 8.资金性质, 9.实际金额, 10.实际币种, 11.收入, 12.支出, 
                # 13.余额, 14.经手人, 15.备注
                return [
                    sn, now_ts, now_ts, s, p, a, i, pr, 
                    round(float(raw_v), 2),  # 第9列：实际金额
                    raw_c,                   # 第10列：实际币种
                    round(float(inc), 2),    # 第11列：收入(USD)
                    round(float(exp), 2),    # 第12列：支出(USD)
                    0,                       # 第13列：余额 (后面代码会统一重算)
                    h, n                     # 第14,15列：经手人, 备注
                ]

            if is_transfer:
                # 转出：实际金额也记为 val_amt
                new_rows.append(create_row(0, f"【转出】{val_sum}", "内部调拨", val_acc_from, val_inv, val_prop, val_amt, val_curr, 0, converted_usd, val_hand, val_note))
                # 转入：实际金额也记为 val_amt
                new_rows.append(create_row(1, f"【转入】{val_sum}", "内部调拨", val_acc_to, val_inv, val_prop, val_amt, val_curr, converted_usd, 0, val_hand, val_note))
            else:
                inc_val = converted_usd if (val_prop in CORE_BIZ[:5] or val_prop in INC_OTHER) else 0
                exp_val = converted_usd if (val_prop in CORE_BIZ[5:] or val_prop in EXP_OTHER) else 0
                # 正常录入
                new_rows.append(create_row(0, val_sum, val_proj, val_acc, val_inv, val_prop, val_amt, val_curr, inc_val, exp_val, val_hand, val_note))
           # --- 3. 合并并重算余额 (全列强制保留2位小数显示) ---
            new_df = pd.DataFrame(new_rows, columns=current_df.columns)
            full_df = pd.concat([current_df, new_df], ignore_index=True)
            
            # 确保数据是数值类型进行计算
            full_df['收入'] = pd.to_numeric(full_df['收入'], errors='coerce').fillna(0)
            full_df['支出'] = pd.to_numeric(full_df['支出'], errors='coerce').fillna(0)
            
            # --- 核心计算环节 ---
            # 1. 安全处理：先把可能存在的逗号去掉，再转为数字，确保计算不出错
            for col in ['收入', '支出']:
                full_df[col] = (
                    full_df[col].astype(str)
                    .str.replace(',', '', regex=False)
                    .pipe(pd.to_numeric, errors='coerce')
                    .fillna(0)
                )

            # 2. 重新计算余额流水
            full_df['余额'] = (full_df['收入'].cumsum() - full_df['支出'].cumsum())

            # 3. 核心修正：将金额列转换为带2位小数的字符串 (不带逗号存入)
            # 这样上传到 Google Sheets 后，由表格的“财务格式”来负责显示逗号
            for col in ['收入', '支出', '余额']:
                full_df[col] = full_df[col].apply(lambda x: "{:.2f}".format(float(x)))
            
            # --- 4. 同步 Google Sheets ---
            conn.update(worksheet="Summary", data=full_df)
            return True
        except Exception as e:
            st.error(f"❌ 写入失败: {e}")
            return False

    # --- 7. 底部按钮区域 ---
    st.divider() # 加上分割线更有层次感
    col_sub, col_can = st.columns(2)

    # 1. 提交按钮
    if col_sub.button("🚀 确认提交", type="primary", use_container_width=True):
        with st.spinner("正在同步至云端..."):
            if validate_and_submit():
                st.toast("记账成功！数据已实时同步", icon="💰")
                st.balloons()
                st.cache_data.clear() # 清除缓存确保主页看到最新数据
                time.sleep(1.2)
                st.rerun()

    # 2. 取消按钮
    if col_can.button("🗑️ 取消返回", use_container_width=True):
        st.rerun()

    # 如果你之前有手动开启的 div 标签，记得闭合它
    st.markdown('</div>', unsafe_allow_html=True)
    
# --- 5. 修正弹窗 (修复报错与对齐) ---
@st.dialog("🛠️ 数据修正", width="large")
def edit_dialog(df):
    target = st.selectbox("第一步：选择要修改的录入编号", ["-- 请选择 --"] + df["录入编号"].tolist()[::-1])
    if target != "-- 请选择 --":
        old = df[df["录入编号"] == target].iloc[0]
        
        c1, c2 = st.columns(2)
        u_date = c1.text_input("日期", value=str(old.get("日期", "")))
        u_inc = c2.number_input("收入 (USD)", value=float(old.get("收入", 0)))
        
        c3, c4 = st.columns(2)
        u_sum = c3.text_input("摘要内容", value=str(old.get("摘要", "")))
        u_exp = c4.number_input("支出 (USD)", value=float(old.get("支出", 0)))
        
        c5, c6 = st.columns(2)
        u_proj = c5.text_input("客户/项目信息", value=str(old.get("客户/项目信息", "")))
        u_hand = c6.text_input("经手人", value=str(old.get("经手人", "")))
        
        c7, c8 = st.columns(2)
        u_acc = c7.text_input("结算账户", value=str(old.get("结算账户", "")))
        u_inv = c8.text_input("审批/发票单号", value=str(old.get("审批/发票单号", "")))
        
        u_prop = st.selectbox("资金性质", ["工程收入", "施工成本", "管理费用", "预收款", "其他"])
        u_note = st.text_area("备注详情", value=str(old.get("备注", "")))

        st.divider()
        sv, ex = st.columns(2)
        if sv.button("💾 确认保存", type="primary", use_container_width=True):
            st.balloons()
            st.success("修正成功！")
            time.sleep(1.2)
            st.cache_data.clear()
            st.rerun()
        st.markdown('<div class="red-btn">', unsafe_allow_html=True)
        if ex.button("❌ 放弃修正", use_container_width=True): st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

# --- 6. 主页面 ---
st.header("📊 汇总统计")
df_main = load_data()

if df_main.empty:
    st.warning("⚠️ 数据库目前没有数据，请点击下方按钮开始录入第一笔账单。")
    if st.button("➕ 立即录入"):
        entry_dialog()
    st.stop()

# --- 第一步：数据预处理 ---
df_main['提交时间'] = pd.to_datetime(df_main['提交时间'], errors='coerce')
df_main = df_main.dropna(subset=['提交时间'])

year_list = sorted(df_main['提交时间'].dt.year.unique().tolist(), reverse=True)
month_list = list(range(1, 13))

# --- 第二步：时间维度看板 ---
with st.container(border=True):
    st.markdown("#### 📅 时间维度看板") 
    
    c1, c2, c3 = st.columns([2, 2, 5]) 
    with c1:
        sel_year = st.selectbox("年份", year_list, index=0, label_visibility="collapsed")
    with c2:
        sel_month = st.selectbox("月份", month_list, index=datetime.now().month - 1, label_visibility="collapsed")
    
    # 计算月份数值
    df_this_month = df_main[(df_main['提交时间'].dt.month == sel_month) & (df_main['提交时间'].dt.year == sel_year)]
    
    lm = 12 if sel_month == 1 else sel_month - 1
    ly = sel_year - 1 if sel_month == 1 else sel_year
    df_last_month = df_main[(df_main['提交时间'].dt.month == lm) & (df_main['提交时间'].dt.year == ly)]
    
    tm_inc = df_this_month['收入'].sum()
    tm_exp = df_this_month['支出'].sum()
    lm_inc = df_last_month['收入'].sum()
    lm_exp = df_last_month['支出'].sum()
    inc_delta = tm_inc - lm_inc
    exp_delta = tm_exp - lm_exp
    t_balance = df_main['收入'].sum() - df_main['支出'].sum()

    with c3:
        st.markdown(f"""
            <div style="margin-top: 7px; padding-left: 5px;">
                <span style="font-size: 1.2rem; font-weight: bold; color: #31333F;">
                    💡 当前统计周期：<span style="color: #4CAF50;">{sel_year}年{sel_month}月</span>
                </span>
            </div>
            """, unsafe_allow_html=True)
    st.markdown("---")
    
    m1, m2, m3 = st.columns(3)
    m1.metric(f"💰 {sel_month}月收入", f"${tm_inc:,.2f}", delta=f"{inc_delta:,.2f}")
    m2.metric(f"📉 {sel_month}月支出", f"${tm_exp:,.2f}", delta=f"{exp_delta:,.2f}", delta_color="inverse")
    m3.metric("🏦 累计总结余", f"${t_balance:,.2f}")

st.divider()

# --- 账户余额与排行 ---
col_l, col_r = st.columns(2)
with col_l:
    st.write("🏦 **各账户当前余额 (原币对账)**")
        
    def calc_bank_balance(group):
        # 1. 统一转为数值
        inc_clean = pd.to_numeric(group['收入'], errors='coerce').fillna(0)
        exp_clean = pd.to_numeric(group['支出'], errors='coerce').fillna(0)
        amt_clean = pd.to_numeric(group['实际金额'], errors='coerce').fillna(0)
        
        # 2. 定义内部计算逻辑
        def get_raw_val(idx):
            current_val = amt_clean.loc[idx]
            if current_val == 0 or pd.isna(current_val):
                if inc_clean.loc[idx] > 0:
                    current_val = inc_clean.loc[idx]
                elif exp_clean.loc[idx] > 0:
                    current_val = exp_clean.loc[idx]
                else:
                    current_val = 0
            is_expense = exp_clean.loc[idx] > 0
            return -current_val if is_expense else current_val

        # --- 核心修复区：确保这些变量在 return 之前被定义 ---
        # 3. 计算 USD 总余额
        usd_bal = inc_clean.sum() - exp_clean.sum()
        
        # 4. 计算原币总余额 (这里定义了 raw_bal)
        raw_bal = sum(get_raw_val(idx) for idx in group.index)
        
        # 5. 获取币种
        valid_currencies = group['实际币种'][group['实际币种'] != ""].tolist()
        cur_name = valid_currencies[-1] if valid_currencies else "USD"
        
        # 6. 返回结果
        return pd.Series([usd_bal, raw_bal, cur_name], index=['USD', 'RAW', 'CUR'])

    try:
        # 分组计算每个账户的统计量
        acc_stats = df_main.groupby('结算账户').apply(calc_bank_balance).reset_index()
        
        # 定义符号映射表（涵盖中英文，防止录入不规范）
        sym_map = {
            "人民币": "¥", "RMB": "¥", "CNY": "¥", 
            "港币": "HK$", "HKD": "HK$", 
            "印尼盾": "Rp", "IDR": "Rp", 
            "越南盾": "₫", "VND": "₫", 
            "美元": "$", "USD": "$"
        }
        
        # 格式化显示：处理负号、符号和千分位
        acc_stats['银行卡实际金额'] = acc_stats.apply(
            lambda r: f"{'-' if r['RAW'] < -0.01 else ''}{sym_map.get(r['CUR'], '$')}{abs(r['RAW']):,.2f}", 
            axis=1
        )
        
        st.dataframe(
            acc_stats[['结算账户', 'USD', '银行卡实际金额']], 
            column_config={
                "USD": st.column_config.NumberColumn("折合美元", format="$%.2f"),
                "银行卡实际金额": "银行对账单余额"
            },
            use_container_width=True, 
            hide_index=True
        )
    except Exception as e:
        st.error(f"余额计算异常: {e}")

with col_r:
    st.write(f"🏷️ **{sel_month}月支出排行**")
    # 筛选本月支出数据并按性质分组
    exp_stats = df_this_month[df_this_month['支出'] > 0].groupby('资金性质')['支出'].sum().sort_values(ascending=False).reset_index()
    if not exp_stats.empty:
        st.dataframe(
            exp_stats.style.format({"支出": "${:,.2f}"}), 
            use_container_width=True, 
            hide_index=True
        )
    else:
        st.caption("该月暂无支出记录")

st.divider()

# --- 第四步：流水明细表 ---
# 1. 先准备数据（确保变量在被使用前已经生成）
df_display = df_main.copy()
df_display = df_display[
    (df_display['提交时间'].dt.year == sel_year) & 
    (df_display['提交时间'].dt.month == sel_month)
]
df_display = df_display.sort_values("录入编号", ascending=False)

# 2. 再进入容器渲染 UI
with st.container(border=True):
    h_col, b_dl, b_add, b_edit = st.columns([4, 1.2, 1, 1])
    h_col.markdown("### 📑 流水明细表")
    
    with b_add:
        if st.button("➕ 录入", type="primary", use_container_width=True, key="main_add"): 
            entry_dialog()
    with b_edit:
        if st.button("🛠️ 修正", type="primary", use_container_width=True, key="main_edit"): 
            edit_dialog(df_main)

    # 搜索框逻辑
    search_query = st.text_input("🔍 搜索本月流水", placeholder="🔍 输入关键词...", label_visibility="collapsed")
    if search_query:
        q = search_query.lower()
        mask = (
            df_display['摘要'].astype(str).str.lower().str.contains(q, na=False) |
            df_display['客户/项目信息'].astype(str).str.lower().str.contains(q, na=False)
        )
        df_display = df_display[mask]

    # 表格显示逻辑
    if not df_display.empty:
        st.dataframe(
            df_display,
            use_container_width=True,
            hide_index=True,
            height=500,
            column_config={
                "录入编号": st.column_config.TextColumn("录入编号", width="small"),
                "摘要": st.column_config.TextColumn("摘要", width="large"),
                "客户/项目信息": st.column_config.TextColumn("客户/项目信息", width="medium"),
                "结算账户": st.column_config.TextColumn("结算账户", width="medium"),
                "审批/发票单号": st.column_config.TextColumn("审批/发票单号", width="medium"),
                "资金性质": st.column_config.TextColumn("资金性质", width="small"),
                "实际金额": st.column_config.NumberColumn("流水原数", format="%.2f", width="small"),
                "实际币种": st.column_config.TextColumn("实际币种", width="small"),
                "收入": st.column_config.NumberColumn("收入(USD)", format="$%.2f"),
                "支出": st.column_config.NumberColumn("支出(USD)", format="$%.2f"),
                "余额": st.column_config.NumberColumn("余额(USD)", format="$%.2f"),
                "经手人": st.column_config.TextColumn("经手人", width="small"),
                "备注": st.column_config.TextColumn("备注", width="medium"),
            }
        )
    else:
        st.info(f"💡 {sel_year}年{sel_month}月 暂无流水记录，您可以尝试切换月份或点击录入。")


