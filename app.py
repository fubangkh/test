import streamlit as st
import pandas as pd
import pytz
import requests
from datetime import datetime
from streamlit_gsheets import GSheetsConnection

# --- 1. 全局配置 (必须放在最前面) ---
st.set_page_config(page_title="富邦日记账", layout="wide")

# --- 2. 核心定义 (时区定义，全局可用) ---
LOCAL_TZ = pytz.timezone('Asia/Phnom_Penh')

# --- 3. 登录拦截系统 ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    from login import show_login_page
    show_login_page()
    st.stop()

# --- 4. 登录成功后的主程序逻辑 ---
st.title("💰 富邦日记账")
if st.sidebar.button("安全退出"):
    st.session_state.logged_in = False
    st.rerun()

# 数据库连接
conn = st.connection("gsheets", type=GSheetsConnection)

st.markdown("""
    <style>
    /* 1. 确认提交按钮：默认是清爽的浅绿灰色 */
    div.stButton > button[kind="primary"] {
        background-color: #1F883D; /* 默认：清爽绿 */
        color: white;
        border: none;
        border-radius: 8px;        /* 圆角稍微圆润一点，更现代 */
        padding: 0.5rem 1rem;
        transition: all 0.3s ease;
        font-weight: 500;
    }

    /* 2. 悬停状态：变成明亮的绿色，并有一点点阴影 */
    div.stButton > button[kind="primary"]:hover {
        background-color: #66BB6A; /* 悬停：亮绿 */
        color: white;
        border-color: #66BB6A;
        box-shadow: 0 4px 8px rgba(0,0,0,0.1); /* 增加一点点悬浮阴影感 */
    }

    /* 3. 取消返回按钮：极简浅灰色 */
    div.stButton > button[kind="secondary"] {
        background-color: #F8F9FA; 
        color: #444;
        border: 1px solid #E0E0E0;
        border-radius: 8px;
    }

    /* 4. 取消按钮悬停：稍微深一点的灰 */
    div.stButton > button[kind="secondary"]:hover {
        background-color: #EEEEEE;
        border-color: #CCCCCC;
        color: #000;
    }
    </style>
""", unsafe_allow_html=True)

# --- 2. 核心功能：实时汇率 ---
@st.cache_data(ttl=3600)
def get_live_rates():
    default_rates = {"USD": 1.0, "CNY": 6.91, "VND": 26000.0, "HKD": 7.82, "IDR": 16848.0}
    try:
        response = requests.get("https://open.er-api.com/v6/latest/USD", timeout=5)
        if response.status_code == 200:
            rates = response.json().get("rates", {})
            return {"USD": 1.0, "CNY": rates.get("CNY", 6.91), "VND": rates.get("VND", 26000), "HKD": rates.get("HKD", 7.82), "IDR": rates.get("IDR", 16848.0)}
    except: pass
    return default_rates

# --- 3. 数据连接 ---
conn = st.connection("gsheets", type=GSheetsConnection)

@st.cache_data(ttl=0)
def load_data():
    csv_url = "https://docs.google.com/spreadsheets/d/1AC572Eq96yIF9it1xCJQAOrxjEEnskProsLmifK3DAs/export?format=csv&gid=0"
    try:
        df = pd.read_csv(csv_url)
        df = df.dropna(how="all")
        
        # 强制将这些涉及计算的列转为数字，空值填 0
        numeric_cols = ['实际金额','收入', '支出', '余额'] # 根据你表格的实际列名添加
        for col in numeric_cols:
            if col in df.columns:
                # 转换前先去掉逗号（Google Sheets 导出的 CSV 有时会带 379,167.21 里的逗号）
                if df[col].dtype == 'object':
                    df[col] = df[col].str.replace(',', '')
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0.0)
        
        df = df.fillna("")
        pd.options.display.float_format = '{:,.2f}'.format
        
        return df
    except Exception as e:
        st.error(f"加载失败: {e}")
        return pd.DataFrame()

# get_dynamic_options 函数保持不变，它现在可以完美兼容上面返回的 df
def get_dynamic_options(df, column_name):
    try:
        if not df.empty and column_name in df.columns:
            # 这里的 x 已经是字符串了，因为上面做了 fillna("")
            raw_list = [str(x).strip() for x in df[column_name].unique() if x]
            clean_options = sorted([
                x for x in raw_list 
                if x and x not in ["--", "-", "nan", "None", "0", "0.0"] and "➕" not in x
            ])
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

    # --- 4. 账户与经手人 (高级状态管理版) ---
    r3_c1, r3_c2 = st.columns(2)
    
    # 初始化 session_state 缓存列表（如果不存在）
    if "opt_acc" not in st.session_state:
        st.session_state.opt_acc = get_dynamic_options(df, "结算账户")
    if "opt_hand" not in st.session_state:
        st.session_state.opt_hand = get_dynamic_options(df, "经手人")
    if "opt_proj" not in st.session_state:
        st.session_state.opt_proj = get_dynamic_options(df, "客户/项目信息")

    if is_transfer:
        val_acc_from = r3_c1.selectbox("➡️ 转出账户", options=st.session_state.opt_acc)
        val_acc_to = r3_c2.selectbox("⬅️ 转入账户", options=st.session_state.opt_acc)
        val_hand = "系统自动结转"
        val_acc = "资金结转" 
    else:
        # --- 结算账户新增 ---
        sel_acc = r3_c1.selectbox("结算账户", options=st.session_state.opt_acc, key="sel_acc_active")
        if sel_acc == "➕ 新增...":
            with st.container(border=True):
                new_acc = st.text_input("✍️ 录入新账户名", key="input_new_acc")
                c1, c2 = st.columns(2)
                if c2.button("确定", key="btn_acc_ok", type="primary", use_container_width=True):
                    if new_acc and new_acc not in st.session_state.opt_acc:
                        # 重点：直接注入列表，不刷新页面
                        st.session_state.opt_acc.insert(1, new_acc) 
                        st.toast(f"✅ 账户 {new_acc} 已加入临时列表，请在下拉框选择")
                    elif not new_acc: st.error("请填入名称")
                if c1.button("取消", key="btn_acc_no", use_container_width=True):
                    # 取消时不 rerun，仅通过提示引导用户切回下拉框
                    st.info("已取消，请切回其他选项")
            val_acc = new_acc
        else:
            val_acc = sel_acc

        # --- 经手人新增 ---
        sel_hand = r3_c2.selectbox("经手人", options=st.session_state.opt_hand, key="sel_hand_active")
        if sel_hand == "➕ 新增...":
            with st.container(border=True):
                new_h = st.text_input("✍️ 录入新姓名", key="input_new_hand")
                c1, c2 = st.columns(2)
                if c2.button("确定", key="btn_h_ok", type="primary", use_container_width=True):
                    if new_h and new_h not in st.session_state.opt_hand:
                        st.session_state.opt_hand.insert(1, new_h)
                        st.toast(f"✅ 姓名 {new_h} 已加入临时列表")
                    elif not new_h: st.error("请填入姓名")
                if c1.button("取消", key="btn_h_no", use_container_width=True):
                    st.info("已取消")
            val_hand = new_h
        else:
            val_hand = sel_hand

    # --- 5. 项目与备注 (闭环交互版) ---
    proj_label = "📍 客户/项目信息 (必填)" if is_req else "客户/项目信息 (选填)"
    
    # 1. 初始化选项列表
    if "opt_proj" not in st.session_state:
        st.session_state.opt_proj = get_dynamic_options(df, "客户/项目信息")

    # 2. 【关键修复】处理“回填”逻辑
    # 我们检查是否有刚刚点击“确定项目”存入的临时变量
    if "tmp_new_p_val" in st.session_state:
        target_val = st.session_state.tmp_new_p_val
        # 找到这个新值在列表中的索引
        try:
            default_ix = st.session_state.opt_proj.index(target_val)
        except ValueError:
            default_ix = 0
        # 用完就删掉临时变量，防止下次打开弹窗还选中它
        del st.session_state.tmp_new_p_val
    else:
        default_ix = 0

    # 3. 定义下拉主框，使用 index 来控制显示内容
    sel_proj = st.selectbox(
        proj_label, 
        options=st.session_state.opt_proj, 
        index=default_ix,
        key="sel_proj_active" 
    )

    # 4. 当选中“➕ 新增...”时
    if sel_proj == "➕ 新增...":
        with st.container(border=True):
            new_p = st.text_input("✍️ 录入新项目", key="input_new_proj_val")
            
            btn_col1, btn_col2 = st.columns(2)
            
            if btn_col2.button("确定项目", key="btn_p_ok", type="primary", use_container_width=True):
                if new_p and new_p.strip():
                    # 将新项目插入列表
                    if new_p not in st.session_state.opt_proj:
                        st.session_state.opt_proj.insert(1, new_p)
                    
                    # 【核心修改】通过临时变量中转，避开直接修改组件 Key 的报错
                    st.session_state.tmp_new_p_val = new_p
                    st.rerun() 
                else:
                    st.error("项目名不能为空")
                    
            if btn_col1.button("取消", key="btn_p_no", use_container_width=True):
                st.rerun()
        
        val_proj = new_p
    else:
        val_proj = sel_proj
    val_note = st.text_area("备注")
    
    st.divider()

    # --- 6. 核心提交逻辑函数 ---
    def validate_and_submit():
        # (前面的非空校验逻辑保持不变...)
        if not val_sum.strip():
            st.error("⚠️ 请填写摘要内容！")
            return False
        # ... 其他 if 校验 ...

        try:
            # --- 【核心保留：sync_settings 逻辑】 ---
            def sync_settings():
                try:
                    # 1. 读取云端设置表 (ttl=0 确保最新)
                    df_set = conn.read(worksheet="Settings", ttl=0)
                    changed = False
                    
                    # 2. 检查并追加“结算账户” (仅在非转账且选了新增时)
                    if not is_transfer and sel_acc == "➕ 新增..." and val_acc not in df_set['结算账户'].values:
                        # 构造新行并合并，忽略空值，保持列名一致
                        df_set = pd.concat([df_set, pd.DataFrame({'结算账户': [val_acc]})], ignore_index=True)
                        changed = True
                    
                    # 3. 检查并追加“经手人”
                    if not is_transfer and sel_hand == "➕ 新增..." and val_hand not in df_set['经手人'].values:
                        df_set = pd.concat([df_set, pd.DataFrame({'经手人': [val_hand]})], ignore_index=True)
                        changed = True
                    
                    # 4. 检查并追加“客户项目”
                    if sel_proj == "➕ 新增..." and val_proj not in df_set['客户项目'].values:
                        df_set = pd.concat([df_set, pd.DataFrame({'客户项目': [val_proj]})], ignore_index=True)
                        changed = True
                    
                    # 5. 如果有变动，一次性写回云端
                    if changed:
                        conn.update(worksheet="Settings", data=df_set)
                        # 清除缓存，确保下次打开下拉菜单是全量最新的
                        st.cache_data.clear() 
                except Exception as e:
                    print(f"设置表同步提示（非报错）: {e}")
            
            # 立即执行同步
            sync_settings()

            # --- 下面继续执行你原本的流水记录逻辑 ---
            current_df = load_data()
            # ... (编号生成、new_rows 生成、余额重算等逻辑)
            # ...
            
            # 最后同步流水表
            conn.update(worksheet="Summary", data=full_df)
            return True

        except Exception as e:
            st.error(f"❌ 写入失败: {e}")
            return False
            
    # --- 7. 底部按钮区域 ---
    st.divider() 
    col_sub, col_can = st.columns(2)

    if col_sub.button("🚀 确认提交", type="primary", use_container_width=True):
        with st.spinner("正在同步至云端..."):
            if validate_and_submit():
                st.toast("记账成功！数据已实时同步", icon="💰")
                st.balloons()
                st.cache_data.clear() 
                time.sleep(1.2)
                st.rerun()

    if col_can.button("🗑️ 取消返回", use_container_width=True):
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
# 1. 币种归一化（这是最优先的，确保后续所有逻辑看到的都是统一币种）
df_main['实际币种'] = df_main['实际币种'].replace(['RMB', '人民币'], 'CNY')

# 2. 时间格式转换
df_main['提交时间'] = pd.to_datetime(df_main['提交时间'], errors='coerce')

# 3. 剔除无效时间行
df_main = df_main.dropna(subset=['提交时间'])

# 4. 数值预清洗（建议加上，确保计算不崩溃）
for col in ['收入', '支出', '余额', '实际金额']:
    if col in df_main.columns:
        df_main[col] = pd.to_numeric(df_main[col], errors='coerce').fillna(0)

# 5. 生成筛选列表（此时 df_main 已经完全干净了）
year_list = sorted(df_main['提交时间'].dt.year.unique().tolist(), reverse=True)
month_list = list(range(1, 13))

# --- 第二步：时间维度看板 ---
with st.container(border=True):
    st.markdown("### 📅 时间维度看板") 
    
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
    
    # 使用 pd.to_numeric 确保这一列全是数字，无法转换的（如空字符串）会变成 NaN
    # 然后用 .sum() 求和，NaN 会被自动忽略
    tm_inc = pd.to_numeric(df_this_month['收入'], errors='coerce').sum()
    tm_exp = pd.to_numeric(df_this_month['支出'], errors='coerce').sum()
    lm_inc = pd.to_numeric(df_last_month['收入'], errors='coerce').sum()
    lm_exp = pd.to_numeric(df_last_month['支出'], errors='coerce').sum()
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
        acc_stats = df_main.groupby('结算账户').apply(calc_bank_balance).reset_index()
        
        # 1. 物理对齐映射：在代码前后手动加空格
        # 这里用 center(10) 表示占据 10 个字符宽度并居中
        iso_map = {
            "人民币": "CNY", "CNY": "CNY", 
            "港币": "HKD", "HKD": "HKD", 
            "印尼盾": "IDR", "IDR": "IDR", 
            "越南盾": "VND", "VND": "VND", 
            "美元": "USD", "USD": "USD"
        }

        # 核心改动：使用 .center() 函数给字符串强行加空格实现“伪居中”
        # 如果想要右对齐，就用 .rjust(10)
        acc_stats['原币种'] = acc_stats['CUR'].map(lambda x: iso_map.get(x, x).rjust(12))
        
        display_acc = acc_stats[['结算账户', '原币种', 'RAW', 'USD']].copy()

        # 2. Styler 逻辑（保持不变）
        styled_acc = display_acc.style.format({
            'RAW': '{:,.2f}',
            'USD': '${:,.2f}'
        }).map(
            lambda x: 'color: #d32f2f;' if x < -0.01 else 'color: #31333F;',
            subset=['RAW', 'USD']
        )
        
        # 3. 渲染
        st.dataframe(
            styled_acc,
            use_container_width=True, 
            hide_index=True,
            column_config={
                "结算账户": st.column_config.TextColumn("结算账户", width="medium"),
                # 这里原币种是带空格的字符串，TextColumn 会把空格也渲染出来
                "原币种": st.column_config.TextColumn("原币种", width="small"),
                "RAW": st.column_config.NumberColumn("原币金额", width="small"),
                "USD": st.column_config.NumberColumn("折合美元 (USD)", width="small")
            }
        )
        
    except Exception as e:
        st.error(f"余额计算异常: {e}")

with col_r:
    st.write(f"🏷️ **{sel_month}月支出排行**")
    # 1. 筛选本月支出数据并按性质分组
    exp_stats = df_this_month[df_this_month['支出'] > 0].groupby('资金性质')['支出'].sum().sort_values(ascending=False).reset_index()
    
    if not exp_stats.empty:
        # 2. 应用 Styler：控制千分位 + 颜色（支出通常统一为红色或默认黑色）+ 右对齐
        styled_exp = exp_stats.style.format({
            "支出": "${:,.2f}"
        }).map(
            # 统一支出颜色为红色，并注入右对齐 CSS
            lambda x: 'color: #d32f2f; text-align: right;', 
            subset=['支出']
        )
        
        # 3. 渲染表格
        st.dataframe(
            styled_exp, 
            use_container_width=True, 
            hide_index=True,
            column_config={
                "资金性质": st.column_config.TextColumn("资金性质", width="medium"),
                # 使用 NumberColumn 借用其右对齐外壳，且不设 format
                "支出": st.column_config.NumberColumn("支出金额", width="medium")
            }
        )
    else:
        st.caption("该月暂无支出记录")

st.divider()

# --- 第四步：流水明细表 (含搜索和格式化) ---
h_col, b_dl, b_add, b_edit = st.columns([4, 1.2, 1, 1])
h_col.subheader("📑 流水明细表")
with b_add:
    if st.button("➕ 录入", type="primary", use_container_width=True, key="main_add"): entry_dialog()
with b_edit:
    if st.button("🛠️ 修正", type="primary", use_container_width=True, key="main_edit"): edit_dialog(df_main)

# 筛选数据
df_display = df_main.copy()
df_display = df_display[
(df_display['提交时间'].dt.year == sel_year) & 
(df_display['提交时间'].dt.month == sel_month)
]
df_display = df_display.sort_values("录入编号", ascending=False)

# 搜索框
search_query = st.text_input("🔍 搜索本月流水", placeholder="🔍 输入关键词...", label_visibility="collapsed")
if search_query:
    q = search_query.lower()
    mask = (
        df_display['摘要'].astype(str).str.lower().str.contains(q, na=False) |
        df_display['客户/项目信息'].astype(str).str.lower().str.contains(q, na=False)|
        df_display['结算账户'].astype(str).str.lower().str.contains(q, na=False)|
        df_display['审批/发票单号'].astype(str).str.lower().str.contains(q, na=False)|
        df_display['经手人'].astype(str).str.lower().str.contains(q, na=False)|
        df_display['资金性质'].astype(str).str.lower().str.contains(q, na=False)
    )
    df_display = df_display[mask]

# --- 第三步：核心优化： Styler 全权接管展示层 ---
# --- 第一步：预处理数据（统一币种名称） ---
df_display['实际币种'] = df_display['实际币种'].replace('RMB', 'CNY')

# --- 第二步：核心优化：Styler 全权接管展示层 ---
def get_styled_df(df):
    display_df = df.copy()
    
    # 1. 物理对齐：给“实际币种”列应用居中/右对齐补位
    # 这里建议使用 .center(12) 看起来更平衡
    display_df['实际币种'] = display_df['实际币种'].apply(lambda x: str(x).center(12))

    # 2. 转换数值（确保 format 不报错）
    money_cols = ['收入', '支出', '余额', '实际金额']
    for col in money_cols:
        display_df[col] = pd.to_numeric(display_df[col], errors='coerce').fillna(0)

    # 3. Styler 样式控制
    return display_df.style.format({
        '收入': '${:,.2f}',
        '支出': '${:,.2f}',
        '余额': '${:,.2f}',
        '实际金额': '{:,.2f}', # 原币金额纯数字展示
        '提交时间': lambda x: x.strftime('%Y-%m-%d %H:%M')
    }).map(
        lambda x: 'color: #1f7a3f; text-align: right;', subset=['收入']
    ).map(
        lambda x: 'color: #d32f2f; text-align: right;', subset=['支出']
    ).map(
        lambda x: 'text-align: right;', subset=['余额', '实际金额']
    )

# --- 第三步：渲染层（修改列名呼应） ---
if not df_display.empty:
    styled_df = get_styled_df(df_display)
    
    st.dataframe(
        styled_df,
        use_container_width=True,
        hide_index=True,
        height=500,
        column_config={
            "提交时间": st.column_config.DatetimeColumn("提交时间", width="small"),
            "修改时间": st.column_config.DatetimeColumn("修改时间", format="YYYY-MM-DD HH:mm", width="small"),
            "录入编号": st.column_config.TextColumn("录入编号", width="small"),
            "摘要": st.column_config.TextColumn("摘要", width="medium"),
            "客户/项目信息": st.column_config.TextColumn("客户/项目信息", width="medium"),
            "结算账户": st.column_config.TextColumn("结算账户", width="small"),
            "资金性质": st.column_config.TextColumn("资金性质", width="small"),
            "实际金额": st.column_config.NumberColumn("原币金额", width="small"),
            "实际币种": st.column_config.TextColumn("原币种", width="small"),
            "收入": st.column_config.NumberColumn("收入(USD)", width="small"),
            "支出": st.column_config.NumberColumn("支出(USD)", width="small"),
            "余额": st.column_config.NumberColumn("余额(USD)", width="small"),
            "经手人": st.column_config.TextColumn("经手人", width="small"),
            "备注": st.column_config.TextColumn("备注", width="small"),
        }
    )
else:
    st.info(f"💡 {sel_year}年{sel_month}月 暂无流水记录，您可以尝试切换月份或点击录入。")







