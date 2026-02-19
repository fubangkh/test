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

# --- 2. 数据连接 ---
conn = st.connection("gsheets", type=GSheetsConnection)

@st.cache_data(ttl=0)
def load_data():
    url = "https://docs.google.com/spreadsheets/d/1AC572Eq96yIF9it1xCJQAOrxjEEnskProsLmifK3DAs/export?format=csv&gid=0"
    try:
        df = pd.read_csv(url)
        return df.dropna(how="all")
    except:
        return conn.read(spreadsheet=url, worksheet="Summary", ttl=0).dropna(how="all")

def get_dynamic_options(df, column_name):
    if not df.empty and column_name in df.columns:
        options = sorted([str(x) for x in df[column_name].unique() if x and str(x).strip()])
        return options + ["➕ 新增..."]
    return ["➕ 新增..."]

# --- 3. 录入弹窗 ---
@st.dialog("📝 新增录入", width="large")
def entry_dialog():
    CORE_BIZ = ["工程收入", "施工收入", "产品销售收入", "服务收入", "预收款", "工程成本", "施工成本"]
    ALL_PROPS = CORE_BIZ[:5] + ["网络收入", "其他收入", "借款"] + CORE_BIZ[5:] + ["管理费用", "工资福利", "资金结转"]

    df = load_data()
    
    # 1. 摘要与时间
    c1, c2 = st.columns(2)
    val_sum = c1.text_input("摘要内容", placeholder="请输入流水说明")
    val_time = c2.datetime_input("业务时间", value=datetime.now(LOCAL_TZ))
    
    # 2. 金额
    val_amt = st.number_input("金额 (USD)", min_value=0.0, step=100.0)
    
    st.divider() 

    # 3. 动态逻辑
    val_prop = st.selectbox("资金性质", ALL_PROPS)
    is_transfer = (val_prop == "资金结转")
    
    r3_c1, r3_c2 = st.columns(2)
    if is_transfer:
        val_acc_from = r3_c1.selectbox("➡️ 转出账户", options=get_dynamic_options(df, "账户"))
        val_acc_to = r3_c2.selectbox("⬅️ 转入账户", options=get_dynamic_options(df, "账户"))
        val_hand = "系统自动结转"
        val_proj = "内部调拨"
    else:
        sel_acc = r3_c1.selectbox("结算账户", options=get_dynamic_options(df, "账户"))
        # 【修复1】增加 key，防止数据丢失
        val_acc = st.text_input("✍️ 录入新账户", key="k_new_acc") if sel_acc == "➕ 新增..." else sel_acc
        
        sel_hand = r3_c2.selectbox("经手人", options=get_dynamic_options(df, "经手人"))
        val_hand = st.text_input("✍️ 录入新姓名", key="k_new_hand") if sel_hand == "➕ 新增..." else sel_hand

        sel_proj = st.selectbox("📍 客户/项目信息", options=get_dynamic_options(df, "客户/项目信息"))
        # 【修复2】增加 key，这是修复“➕ 新增...”残留的关键
        val_proj = st.text_input("✍️ 录入新项目", key="k_new_proj") if sel_proj == "➕ 新增..." else sel_proj

    def validate_and_submit():
        if not val_sum.strip():
            st.error("⚠️ 请填写摘要！")
            return False
        
        try:
            current_df = load_data()
            now_ts = datetime.now(LOCAL_TZ).strftime("%Y-%m-%d %H:%M:%S")
            # 简化版写入逻辑
            new_data = [f"R{int(time.time())}", now_ts, now_ts, val_sum, val_proj, 
                        val_acc if not is_transfer else val_acc_from, "", val_prop, 
                        val_amt if not is_transfer else 0, 0, 0, val_hand, ""]
            
            new_df = pd.DataFrame([new_data], columns=current_df.columns)
            full_df = pd.concat([current_df, new_df], ignore_index=True)
            conn.update(worksheet="Summary", data=full_df)
            return True
        except Exception as e:
            st.error(f"❌ 写入失败: {e}")
            return False

    if st.button("✅ 提交并返回", type="primary", use_container_width=True):
        if validate_and_submit():
            st.success("保存成功！")
            st.cache_data.clear()
            time.sleep(1)
            st.rerun()

# --- 4. 主页面逻辑 (严格对齐版) ---
pwd = st.sidebar.text_input("🔑 访问密码", type="password")

if pwd == ADMIN_PWD:
    st.title("📊 财务管理系统")
    df_main = load_data()

    if not df_main.empty:
        # 简单显示总结余
        st.metric("总结余", f"${pd.to_numeric(df_main['余额'], errors='coerce').iloc[-1]:,.2f}")
        
        if st.button("➕ 录入数据", type="primary"):
            st.session_state.entry_dialog_show = True
        
        st.dataframe(df_main.sort_values("录入编号", ascending=False), use_container_width=True)
    else:
        st.info("暂无数据")
        if st.button("➕ 录入第一笔数据"):
            st.session_state.entry_dialog_show = True

    # 【修复3】确保调用名与定义名 entry_dialog 一致
    if st.session_state.get('entry_dialog_show'):
        entry_dialog()
elif pwd:
    st.error("密码不正确")
else:
    st.warning("请在侧边栏输入密码")
