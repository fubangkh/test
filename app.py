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

# --- 4. 录入弹窗 ---
@st.dialog("📝 新增录入", width="large")
def entry_dialog():
    CORE_BIZ = ["工程收入", "施工收入", "产品销售收入", "服务收入", "预收款", "工程成本", "施工成本"]
    INC_OTHER = ["网络收入", "其他收入", "借款", "往来款收回", "押金收回"]
    EXP_OTHER = ["网络成本", "管理费用", "差旅费", "工资福利", "往来款支付", "押金支付", "归还借款"]
    ALL_PROPS = CORE_BIZ[:5] + INC_OTHER + CORE_BIZ[5:] + EXP_OTHER + ["资金结转"]

    df = load_data()
    live_rates = get_live_rates()
    
    current_balance = float(df['余额'].iloc[-1]) if not df.empty else 0
    st.write(f"💡 当前总结余: **${current_balance:,.2f}**")
    
    c1, c2 = st.columns(2)
    val_sum = c1.text_input("摘要内容", placeholder="请输入流水说明", key="in_sum")
    val_time = c2.datetime_input("业务时间", value=datetime.now(LOCAL_TZ))
    
    r2_c1, r2_c2, r2_c3 = st.columns(3)
    val_amt = r2_c1.number_input("金额", min_value=0.0, step=100.0, key="in_amt")
    val_curr = r2_c2.selectbox("币种", list(live_rates.keys()), key="in_curr")
    val_rate = r2_c3.number_input("实时汇率", value=float(live_rates[val_curr]), format="%.4f", key="in_rate")
    
    converted_usd = round(val_amt / val_rate, 2) if val_rate != 0 else 0
    st.info(f"💰 换算后金额：$ {converted_usd:,.2f} USD")
    st.divider() 

    r4_c1, r4_c2 = st.columns(2)
    val_inv = r4_c1.text_input("审批/发票编号", key="in_inv")
    val_prop = r4_c2.selectbox("资金性质", ALL_PROPS, key="in_prop")
    
    is_transfer = (val_prop == "资金结转")
    is_req = val_prop in CORE_BIZ

    r3_c1, r3_c2 = st.columns(2)
    if is_transfer:
        val_acc_from = r3_c1.selectbox("➡️ 转出账户", options=get_dynamic_options(df, "账户"), key="sel_from")
        val_acc_to = r3_c2.selectbox("⬅️ 转入账户", options=get_dynamic_options(df, "账户"), key="sel_to")
        val_acc = f"{val_acc_from}->{val_acc_to}" 
        val_hand = "系统自动结转"
    else:
        sel_acc = r3_c1.selectbox("结算账户", options=get_dynamic_options(df, "账户"), key="sel_acc")
        val_acc = r3_c1.text_input("✍️ 录入新账户", key="new_acc") if sel_acc == "➕ 新增..." else sel_acc
        
        sel_hand = r3_c2.selectbox("经手人", options=get_dynamic_options(df, "经手人"), key="sel_hand")
        val_hand = r3_c2.text_input("✍️ 录入新姓名", key="new_hand") if sel_hand == "➕ 新增..." else sel_hand

    proj_label = "📍 客户/项目名称 (必填)" if is_req else "客户/项目名称 (选填)"
    sel_proj = st.selectbox(proj_label, options=get_dynamic_options(df, "客户/项目名称"), key="sel_proj")
    val_proj = st.text_input("✍️ 录入新项目名称", key="new_proj") if sel_proj == "➕ 新增..." else sel_proj
    val_note = st.text_area("备注详情", key="in_note")
    
    st.divider()

    def validate_and_submit(p_proj, p_acc, p_hand):
        if not val_sum.strip():
            st.error("⚠️ 请填写摘要内容！")
            return False
        if val_amt <= 0:
            st.error("⚠️ 金额必须大于 0！")
            return False
        if is_req and (not p_proj or p_proj == "➕ 新增..."):
            st.error(f"⚠️ 【{val_prop}】必须关联项目！")
            return False
        
        try:
            current_df = load_data()
            now_dt = datetime.now(LOCAL_TZ)
            now_ts = now_dt.strftime("%Y-%m-%d %H:%M:%S")
            today_str = now_dt.strftime("%Y%m%d")

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
                new_rows.append(create_row(0, val_sum, p_proj, p_acc, val_inv, val_prop, inc_val, exp_val, p_hand, val_note))

            new_df = pd.DataFrame(new_rows, columns=current_df.columns)
            full_df = pd.concat([current_df, new_df], ignore_index=True)
            
            for col in ['收入', '支出']:
                full_df[col] = pd.to_numeric(full_df[col].astype(str).str.replace(',', ''), errors='coerce').fillna(0)
            
            full_df['余额'] = full_df['收入'].cumsum() - full_df['支出'].cumsum()

            for col in ['收入', '支出', '余额']:
                full_df[col] = full_df[col].apply(lambda x: "{:.2f}".format(float(x)))
            
            conn.update(worksheet="Summary", data=full_df)
            return True
        except Exception as e:
            st.error(f"❌ 写入失败: {e}")
            return False

    b1, b2, b3 = st.columns(3)
    if b1.button("📥 提交并继续", type="primary", use_container_width=True):
        if validate_and_submit(val_proj, val_acc, val_hand):
            st.toast("✅ 数据已保存")
            st.cache_data.clear()
            time.sleep(1)
            st.rerun()

    if b2.button("✅ 提交并返回", type="primary", use_container_width=True):
        if validate_and_submit(val_proj, val_acc, val_hand):
            st.balloons()
            st.cache_data.clear()
            st.rerun()

    if b3.button("❌ 取消录入", use_container_width=True): st.rerun()

# --- 5. 修正弹窗 ---
@st.dialog("🛠️ 数据修正", width="large")
def edit_dialog(df):
    target = st.selectbox("选择要修改的录入编号", ["-- 请选择 --"] + df["录入编号"].tolist()[::-1])
    if target != "-- 请选择 --":
        old = df[df["录入编号"] == target].iloc[0]
        c1, c2 = st.columns(2)
        u_date = c1.text_input("日期", value=str(old.get("日期", "")))
        u_inc = c2.number_input("收入 (USD)", value=float(old.get("收入", 0)))
        c3, c4 = st.columns(2)
        u_sum = c3.text_input("摘要内容", value=str(old.get("摘要", "")))
        u_exp = c4.number_input("支出 (USD)", value=float(old.get("支出", 0)))
        
        st.divider()
        if st.button("💾 确认保存修正", type="primary", use_container_width=True):
            st.success("修正成功！")
            st.cache_data.clear()
            st.rerun()

# --- 6. 主页面 ---
pwd = st.sidebar.text_input("🔑 访问密码", type="password")
if pwd == ADMIN_PWD:
    st.title("📊 实时汇总统计")
    df_main = load_data()
    
    if not df_main.empty:
        st.metric("总结余", f"${float(df_main['余额'].iloc[-1]):,.2f}")
        st.divider()
        
        h_col, b_dl, b_add, b_edit = st.columns([4, 1.2, 1, 1])
        h_col.subheader("📑 原始流水明细")
        
        with b_add:
            if st.button("➕ 录入", type="primary", use_container_width=True): entry_dialog()
        with b_edit:
            if st.button("🛠️ 修正", type="primary", use_container_width=True): edit_dialog(df_main)

        # 1. 准备显示数据
        df_display = df_main.sort_values("录入编号", ascending=False).copy()
        
        # 2. 格式化金额（仅加逗号，不加右对齐补丁）
        for col in ['收入', '支出', '余额']:
            if col in df_display.columns:
                df_display[col] = pd.to_numeric(df_display[col], errors='coerce').fillna(0).map('{:,.2f}'.format)

        # 3. 显示表格
        st.dataframe(
            df_display,
            use_container_width=True,
            hide_index=True,
            column_config={
                "收入": st.column_config.Column(width="medium"),
                "支出": st.column_config.Column(width="medium"),
                "余额": st.column_config.Column(width="medium"),
                "摘要": st.column_config.TextColumn(width="large"),
                "录入编号": st.column_config.TextColumn(width="small")
            }
        )
else:
    st.info("请输入密码解锁系统")
