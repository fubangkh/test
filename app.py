import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import time
import pytz
import requests
from datetime import datetime

# --- 1. 配置与全局样式 ---
st.set_page_config(page_title="富邦财务系统", layout="wide")
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
    default_rates = {"USD": 1.0, "RMB": 7.23, "VND": 25450.0, "HKD": 7.82}
    try:
        response = requests.get("https://open.er-api.com/v6/latest/USD", timeout=5)
        if response.status_code == 200:
            rates = response.json().get("rates", {})
            return {"USD": 1.0, "RMB": rates.get("CNY", 7.23), "VND": rates.get("VND", 25450), "HKD": rates.get("HKD", 7.82)}
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

# --- 4. 录入弹窗 (全功能合并 + 报错修复版) ---
@st.dialog("📝 数据录入", width="large")
def entry_dialog():
    # --- A. 内部常量定义 (防止 NameError) ---
    CORE_BUSINESS = ["工程收入", "施工收入", "产品销售收入", "服务收入", "预收款", "工程成本", "施工成本"]
    OTHER_INCOME = ["网络收入", "其他收入", "借款", "往来款收回", "押金收回"]
    OTHER_EXPENSE = ["网络成本", "管理费用", "差旅费", "工资福利", "往来款支付", "押金支付", "归还借款"]
    PROPERTIES_LIST = CORE_BUSINESS[:5] + OTHER_INCOME + CORE_BUSINESS[5:] + OTHER_EXPENSE + ["资金结转"]

    df = load_data()
    live_rates = get_live_rates()
    st.write(f"💡 当前系统总结余: **${df['余额'].iloc[-1] if not df.empty else 0:,.2f}**")
    
    # 第一行：摘要与时间
    c1, c2 = st.columns(2)
    val_sum = c1.text_input("摘要内容", placeholder="请输入流水说明")
    val_time = c2.datetime_input("业务时间", value=datetime.now(LOCAL_TZ))
    
    # 第二行：金额、币种、汇率
    r2_c1, r2_c2, r2_c3 = st.columns(3)
    val_amt = r2_c1.number_input("金额", min_value=0.0, step=100.0)
    val_curr = r2_c2.selectbox("币种", list(live_rates.keys()))
    val_rate = r2_c3.number_input("实时汇率 (API获取)", value=float(live_rates[val_curr]), format="%.4f")
    
    # 实时换算显示 (22px 蓝色条样式)
    converted_usd = val_amt / val_rate if val_rate != 0 else 0
    st.markdown(f"""
        <div style="background-color: #f8f9fa; padding: 8px 12px; border-radius: 6px; border-left: 4px solid #0056b3; margin: 5px 0;">
            <span style="font-size: 14px; color: #666; font-weight: bold;">💰 换算后金额估算：</span>
            <span style="font-size: 22px; font-weight: bold; color: #0056b3; margin-left: 10px;">$ {converted_usd:,.2f} <span style="font-size: 14px;">USD</span></span>
        </div>
        """, unsafe_allow_html=True)
    
    st.divider() 

    # 第三行前置：获取资金性质（触发联动）
    r4_c1, r4_c2 = st.columns(2)
    val_inv = r4_c1.text_input("审批/发票编号", placeholder="选填")
    val_prop = r4_c2.selectbox("资金性质", PROPERTIES_LIST)
    
    # 核心判定
    is_transfer = (val_prop == "资金结转")
    is_req = val_prop in CORE_BUSINESS # 包含工程成本和施工成本

    # 第三行：账户与经手人
    r3_c1, r3_c2 = st.columns(2)
    if is_transfer:
        val_acc_from = r3_c1.selectbox("➡️ 转出账户", options=get_dynamic_options(df, "账户"))
        val_acc_to = r3_c2.selectbox("⬅️ 转入账户", options=get_dynamic_options(df, "账户"))
        val_hand = "系统自动结转"
    else:
        sel_acc = r3_c1.selectbox("结算账户", options=get_dynamic_options(df, "账户"))
        val_acc = st.text_input("✍️ 录入新账户名称") if sel_acc == "➕ 新增..." else sel_acc
        sel_hand = r3_c2.selectbox("经手人", options=get_dynamic_options(df, "经手人"))
        val_hand = st.text_input("✍️ 录入新姓名") if sel_hand == "➕ 新增..." else sel_hand

    # 第五行：项目名称联动
    proj_label = "📍 客户/项目名称 (必填)" if is_req else "客户/项目名称 (选填)"
    sel_proj = st.selectbox(proj_label, options=get_dynamic_options(df, "客户/项目名称"))
    val_proj = st.text_input("✍️ 录入新项目") if sel_proj == "➕ 新增..." else sel_proj
    val_note = st.text_area("备注详情")
    
    st.divider()
    # 按钮区域 (严格修正缩进，解决 IndentationError)
    b1, b2, b3 = st.columns(3)

    def validate_and_submit(stay_open):
        if not val_sum.strip():
            st.error("⚠️ 请填写摘要内容！"); return
        if val_amt <= 0:
            st.error("⚠️ 金额必须大于 0！"); return
        if is_req and (not val_proj or val_proj.strip() == ""):
            st.error(f"⚠️ 【{val_prop}】必须关联项目！"); return
        
        # 自动收支判定逻辑
        final_rows = []
        if is_transfer:
            final_rows.append({"日期": val_time.strftime("%Y-%m-%d"), "摘要": f"【转出】{val_sum}", "收入": 0, "支出": converted_usd, "账户": val_acc_from, "资金性质": "资金结转", "客户/项目名称": "内部调拨", "经手人": val_hand, "备注": val_note})
            final_rows.append({"日期": val_time.strftime("%Y-%m-%d"), "摘要": f"【转入】{val_sum}", "收入": converted_usd, "支出": 0, "账户": val_acc_to, "资金性质": "资金结转", "客户/项目名称": "内部调拨", "经手人": val_hand, "备注": val_note})
        else:
            inc = converted_usd if (val_prop in CORE_BUSINESS[:5] or val_prop in OTHER_INCOME) else 0
            exp = converted_usd if (val_prop in CORE_BUSINESS[5:] or val_prop in OTHER_EXPENSE) else 0
            final_rows.append({"日期": val_time.strftime("%Y-%m-%d"), "摘要": val_sum, "收入": inc, "支出": exp, "账户": val_acc, "资金性质": val_prop, "客户/项目名称": val_proj, "经手人": val_hand, "备注": val_note})

        # --- 这里根据您的实际情况添加 Google Sheets 写入逻辑 ---
        
        st.balloons()
        st.success("🎉 数据录入成功！")
        time.sleep(1.2) 
        st.cache_data.clear() 
        st.rerun()

    # 按钮逻辑对齐 (严禁改动缩进)
    if b1.button("📥 提交并继续", type="primary", use_container_width=True):
        validate_and_submit(stay_open=True)

    if b2.button("✅ 提交并返回", type="primary", use_container_width=True):
        validate_and_submit(stay_open=False)

    st.markdown('<div class="red-btn">', unsafe_allow_html=True)
    if b3.button("❌ 取消录入", use_container_width=True): 
        st.rerun()
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
        u_proj = c5.text_input("客户/项目名称", value=str(old.get("客户/项目名称", "")))
        u_hand = c6.text_input("经手人", value=str(old.get("经手人", "")))
        
        c7, c8 = st.columns(2)
        u_acc = c7.text_input("结算账户", value=str(old.get("账户", "")))
        u_inv = c8.text_input("审批/发票编号", value=str(old.get("审批/发票编号", "")))
        
        u_prop = st.selectbox("资金性质", ["工程收入", "施工成本", "管理费用", "预收款", "其他"])
        u_note = st.text_area("备注详情", value=str(old.get("备注", "")))

        st.divider()
        sv, ex = st.columns(2)
        if sv.button("💾 确认保存修正", type="primary", use_container_width=True):
            st.balloons()
            st.success("修正成功！")
            time.sleep(1.2)
            st.cache_data.clear()
            st.rerun()
        st.markdown('<div class="red-btn">', unsafe_allow_html=True)
        if ex.button("❌ 放弃修正", use_container_width=True): st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

# --- 6. 主页面 ---
pwd = st.sidebar.text_input("🔑 访问密码", type="password")
if pwd == ADMIN_PWD:
    st.title("📊 财务实时汇总统计")
    df_main = load_data()
    if not df_main.empty:
        st.metric("总结余", f"${df_main['余额'].iloc[-1]:,.2f}")
        st.divider()
        h_col, b_dl, b_add, b_edit = st.columns([4, 1.2, 1, 1])
        h_col.subheader("📑 原始流水明细")
        with b_add:
            if st.button("➕ 录入", type="primary", use_container_width=True): entry_dialog()
        with b_edit:
            if st.button("🛠️ 修正", type="primary", use_container_width=True): edit_dialog(df_main)
        st.dataframe(df_main.sort_values("录入编号", ascending=False), use_container_width=True, hide_index=True)
else:
    st.info("请输入密码解锁系统")






