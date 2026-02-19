import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import time
import pytz
import requests
from datetime import datetime

# --- 1. 配置与全局样式 ---
st.set_page_config(page_title="富邦日记账", layout="wide")
ADMIN_PWD = "123"
LOCAL_TZ = pytz.timezone('Asia/Phnom_Penh')

st.markdown("""
    <style>
    div.stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #0056b3 0%, #007bff 100%) !important;
        color: white !important; font-size: 20px !important; font-weight: bold !important;
        padding: 10px !important; border-radius: 10px !important;
    }
    .red-btn > div > button {
        color: #ff4b4b !important; border: 1px solid #ff4b4b !important;
        background-color: white !important;
    }
    </style>
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
    return conn.read(worksheet="Summary", ttl=0).dropna(how="all")

def get_dynamic_options(df, column_name):
    if not df.empty and column_name in df.columns:
        options = sorted([str(x) for x in df[column_name].unique() if x and str(x).strip()])
        return options + ["➕ 新增..."]
    return ["➕ 新增..."]

# --- 4. 录入弹窗 (完美版：含汇率、气球及新增Key修复) ---
@st.dialog("📝 新增录入", width="large")
def entry_dialog():
    # A. 内部常量定义
    CORE_BIZ = ["工程收入", "施工收入", "产品销售收入", "服务收入", "预收款", "工程成本", "施工成本"]
    INC_OTHER = ["网络收入", "其他收入", "借款", "往来款收回", "押金收回"]
    EXP_OTHER = ["网络成本", "管理费用", "差旅费", "工资福利", "往来款支付", "押金支付", "归还借款"]
    ALL_PROPS = CORE_BIZ[:5] + INC_OTHER + CORE_BIZ[5:] + EXP_OTHER + ["资金结转"]

    df = load_data()
    live_rates = get_live_rates()
    
    # 顶部结余显示
    try:
        last_bal = str(df['余额'].iloc[-1]).replace(',', '').replace('$', '')
        current_balance = float(last_bal)
    except:
        current_balance = 0.0
    st.write(f"💡 当前总结余: **${current_balance:,.2f}**")
    
    # 1. 摘要与时间
    c1, c2 = st.columns(2)
    val_sum = c1.text_input("摘要内容", placeholder="请输入流水说明")
    val_time = c2.datetime_input("业务时间", value=datetime.now(LOCAL_TZ))
    
    # 2. 金额、币种、汇率
    r2_c1, r2_c2, r2_c3 = st.columns(3)
    val_amt = r2_c1.number_input("金额", min_value=0.0, step=100.0)
    val_curr = r2_c2.selectbox("币种", list(live_rates.keys()))
    val_rate = r2_c3.number_input("实时汇率", value=float(live_rates[val_curr]), format="%.4f")
    
    # 实时换算显示
    converted_usd = round(val_amt / val_rate, 2) if val_rate != 0 else 0
    st.info(f"💰 换算后金额：$ {converted_usd:,.2f} USD")
    
    st.divider() 

    # 3. 性质与发票
    r4_c1, r4_c2 = st.columns(2)
    val_inv = r4_c1.text_input("审批/发票编号")
    val_prop = r4_c2.selectbox("资金性质", ALL_PROPS)
    
    is_transfer = (val_prop == "资金结转")
    is_req = val_prop in CORE_BIZ

    # 4. 账户与经手人 (添加 Key 修复新增失败)
    r3_c1, r3_c2 = st.columns(2)
    if is_transfer:
        val_acc_from = r3_c1.selectbox("➡️ 转出账户", options=get_dynamic_options(df, "账户"))
        val_acc_to = r3_c2.selectbox("⬅️ 转入账户", options=get_dynamic_options(df, "账户"))
        val_hand = "系统自动结转"
        val_proj = "内部调拨"
    else:
        sel_acc = r3_c1.selectbox("结算账户", options=get_dynamic_options(df, "账户"))
        val_acc = st.text_input("✍️ 录入新账户", key="k_new_acc") if sel_acc == "➕ 新增..." else sel_acc
        
        sel_hand = r3_c2.selectbox("经手人", options=get_dynamic_options(df, "经手人"))
        val_hand = st.text_input("✍️ 录入新姓名", key="k_new_hand") if sel_hand == "➕ 新增..." else sel_hand

        # 5. 项目与备注 (添加 Key 修复新增失败)
        proj_label = "📍 客户/项目信息 (必填)" if is_req else "客户/项目信息 (选填)"
        sel_proj = st.selectbox(proj_label, options=get_dynamic_options(df, "客户/项目信息"))
        val_proj = st.text_input("✍️ 录入新项目", key="k_new_proj") if sel_proj == "➕ 新增..." else sel_proj
    
    val_note = st.text_area("备注详情")
    st.divider()

    # --- 6. 核心提交逻辑 ---
    def validate_and_submit():
        if not val_sum.strip():
            st.error("⚠️ 请填写摘要内容！")
            return False
        if val_amt <= 0:
            st.error("⚠️ 金额必须大于 0！")
            return False
        if is_req and (not val_proj or val_proj.strip() == ""):
            st.error(f"⚠️ 【{val_prop}】必须关联项目！")
            return False
        
        try:
            current_df = load_data()
            now_dt = datetime.now(LOCAL_TZ)
            now_ts = now_dt.strftime("%Y-%m-%d %H:%M:%S")
            today_str = now_dt.strftime("%Y%m%d")

            # 编号生成
            today_mask = current_df['录入编号'].astype(str).str.contains(f"R{today_str}", na=False)
            today_records = current_df[today_mask]
            start_num = (int(str(today_records['录入编号'].iloc[-1])[-3:]) + 1) if not today_records.empty else 1

            new_rows = []
            def create_row(offset, s, p, a, i, pr, inc, exp, h, n):
                sn = f"R{today_str}{(start_num + offset):03d}"
                return [sn, now_ts, now_ts, s, p, a, i, pr, round(float(inc), 2), round(float(exp), 2), 0, h, n]

            if is_transfer:
                new_rows.append(create_row(0, f"【转出】{val_sum}", "内部调拨", val_acc_from, val_inv, val_prop, 0, converted_usd, val_hand, val_note))
                new_rows.append(create_row(1, f"【转入】{val_sum}", "内部调拨", val_acc_to, val_inv, val_prop, converted_usd, 0, val_hand, val_note))
            else:
                inc_val = converted_usd if (val_prop in CORE_BIZ[:5] or val_prop in INC_OTHER) else 0
                exp_val = converted_usd if (val_prop in CORE_BIZ[5:] or val_prop in EXP_OTHER) else 0
                new_rows.append(create_row(0, val_sum, val_proj, val_acc, val_inv, val_prop, inc_val, exp_val, val_hand, val_note))

            new_df = pd.DataFrame(new_rows, columns=current_df.columns)
            full_df = pd.concat([current_df, new_df], ignore_index=True)
            
            # 重新计算余额
            for col in ['收入', '支出']:
                full_df[col] = pd.to_numeric(full_df[col].astype(str).str.replace(',', ''), errors='coerce').fillna(0)
            full_df['余额'] = (full_df['收入'].cumsum() - full_df['支出'].cumsum())

            # 格式化回存
            for col in ['收入', '支出', '余额']:
                full_df[col] = full_df[col].apply(lambda x: "{:.2f}".format(float(x)))
            
            conn.update(worksheet="Summary", data=full_df)
            return True
        except Exception as e:
            st.error(f"❌ 写入失败: {e}")
            return False

    # 底部按钮
    b1, b2, b3 = st.columns(3)
    if b1.button("📥 提交并继续", type="primary", use_container_width=True):
        if validate_and_submit():
            st.balloons()
            st.cache_data.clear()
            st.rerun()

    if b2.button("✅ 提交并返回", type="primary", use_container_width=True):
        if validate_and_submit():
            st.balloons()
            st.cache_data.clear()
            st.rerun()

    if b3.button("❌ 取消", use_container_width=True): st.rerun()

# --- 5. 主页面 ---
pwd = st.sidebar.text_input("🔑 访问密码", type="password")
if pwd == ADMIN_PWD:
    st.title("📊 实时汇总统计")
    df_main = load_data()
    
    if not df_main.empty:
        # 显示结余
        try:
            val_bal = str(df_main['余额'].iloc[-1]).replace(',', '').replace('$', '')
            current_bal = float(val_bal)
        except:
            current_bal = 0.0
        st.metric("总结余", f"${current_bal:,.2f}")
        
        st.divider()
        h_col, b_add = st.columns([6, 1])
        h_col.subheader("📑 原始流水明细")
        with b_add:
            if st.button("➕ 录入数据", type="primary", use_container_width=True):
                entry_dialog()

        # 数据表格格式化
        df_display = df_main.sort_values("录入编号", ascending=False).copy()
        for col in ['收入', '支出', '余额']:
            df_display[col] = pd.to_numeric(df_display[col], errors='coerce').fillna(0).map('{:,.2f}'.format)

        st.dataframe(df_display, use_container_width=True, hide_index=True)
    else:
        st.info("暂无数据，请点击录入第一笔数据。")
        if st.button("➕ 录入数据"): entry_dialog()
else:
    if pwd: st.error("密码错误")
    else: st.warning("请输入侧边栏密码以解锁")
