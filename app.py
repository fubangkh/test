import requests
import streamlit as st
from login import show_login_page  # 引入登录逻辑
import pandas as pd
import io
from datetime import datetime
import pytz
from streamlit_gsheets import GSheetsConnection
from logic import get_live_rates, get_dynamic_options, ISO_MAP, prepare_new_data
from logic import ALL_PROPS, CORE_BIZ, INC_OTHER, EXP_OTHER
from forms import entry_dialog, edit_dialog, row_action_dialog

# --- 1. 基础页面配置 ---
st.set_page_config(page_title="富邦日记账", layout="wide", page_icon="📊")
# 登录状态控制
# 初始化登录状态
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

# 如果没登录，直接运行登录页并停止向下执行
if not st.session_state.logged_in:
    show_login_page()
    st.stop()  # 🌟 关键：未登录时拦截后续所有代码运行

# 主界面多语言字典
MAIN_LANG = {
    "zh": {
        "title_main": "富邦日记账",
        "sidebar_title": "⚙️ 侧边栏",
        "month_sel": "选择月份",
        "btn_export": "📥 导出 Excel",
        "table_title": "📊 财务流水明细",
        "stat_total_in": "总收入",
        "stat_total_out": "总支出",
        "stat_balance": "当前结余",
        "table_title": "📊 日常收支",
        "btn_add": "➕ 新增流水录入",
    },
    "en": {
        "title_main": "Fubang Journal",
        "sidebar_title": "Fubang Journal",
        "month_sel": "Select Month",
        "btn_export": "📥 Export Excel",
        "table_title": "📊 Financial Transactions",
        "stat_total_in": "Total Income",
        "stat_total_out": "Total Expense",
        "stat_balance": "Current Balance",
        "table_title": "📊 Statistics Summary",
        "btn_add": "➕ Add New Transaction",
    },
    "km": {
        "title_main": "ហ្វូបង់ សៀវភៅគណនេយ្យោះ",
        "sidebar_title": "ហ្វូបង់ សៀវភៅគណនេយ្យោះ",
        "month_sel": "ជ្រើសរើសខែ",
        "btn_export": "📥 ទាញយក Excel",
        "table_title": "📊 ព័ត៌មានលម្អិតអំពីហិរញ្ញវត្ថុ",
        "stat_total_in": "ចំណូលសរុប",
        "stat_total_out": "ចំណាយសរុប",
        "stat_balance": "សមតុល្យបច្ចុប្បន្ន",
        "table_title": "📊 សេចក្តីសង្ខេបស្ថិតិ",
        "btn_add": "➕ បញ្ចូលទិន្នន័យថ្មី",
    },
    "vi": {
        "title_main": "Sổ Kế Toán Fubang",
        "sidebar_title": "Sổ Kế Toán Fubang",
        "month_sel": "Chọn tháng",
        "btn_export": "📥 Xuất Excel",
        "table_title": "📊 Chi tiết giao dịch tài chính",
        "stat_total_in": "Tổng thu",
        "stat_total_out": "Tổng chi",
        "stat_balance": "Số dư hiện tại",
        "table_title": "📊 Thống kê tổng hợp",
        "btn_add": "➕ Thêm giao dịch mới",
    }
}

# 自动获取当前语言包
L_MAIN = MAIN_LANG.get(st.session_state.lang, MAIN_LANG["zh"])

LOCAL_TZ = pytz.timezone('Asia/Phnom_Penh')

# 初始化全局状态
if "table_version" not in st.session_state:
    st.session_state.table_version = 0
if "show_edit_modal" not in st.session_state:
    st.session_state.show_edit_modal = False
if "edit_target_id" not in st.session_state:
    st.session_state.edit_target_id = None
if "current_active_id" not in st.session_state:
    st.session_state.current_active_id = None

# --- 2. 数据加载函数 ---
conn = st.connection("gsheets", type=GSheetsConnection)

# --- 升级版：企业微信同步函数 ---
def sync_wecom_to_sheets(conn):
    try:
        CORPID = st.secrets["WECOM_CORPID"]
        SECRET = st.secrets["WECOM_SECRET"]
        TEMPLATE_ID = st.secrets["WECOM_TEMPLATE_ID"]
        
        # 1. 获取 Access Token
        token_url = f"https://qyapi.weixin.qq.com/cgi-bin/gettoken?corpid={CORPID}&corpsecret={SECRET}"
        token_res = requests.get(token_url).json()
        token = token_res.get("access_token")
        if not token: return f"❌ Token获取失败: {token_res.get('errmsg')}"

        # 2. 获取最近 7 天已通过审批列表 (sp_status=2)
        import time
        now = int(time.time())
        start_time = str(now - (30 * 24 * 3600))
        list_url = f"https://qyapi.weixin.qq.com/cgi-bin/oa/getapprovalinfo?access_token={token}"
        payload = {
            "starttime": str(now - 604800), "endtime": str(now),
            "cursor": 0, "size": 100,
            "filters": [{"key": "template_id", "value": TEMPLATE_ID}, {"key": "sp_status", "value": "2"}]
        }
        res_list = requests.post(list_url, json=payload).json()
        st.sidebar.write("调试信息:", res_list)
        sp_nos = res_list.get("sp_no_list", [])
        if not sp_nos:
            # 这里的报错信息会根据腾讯返回的内容自动变化
            errmsg = res_list.get("errmsg", "无报错")
            return f"📭 抓取失败。返回码: {res_list.get('errcode')}, 原因: {errmsg}。请确认单据是否在30天内且已完全审批通过。"

        # 3. 读取现有数据去重 (确保 worksheet 名字为 Summary)
        df_existing = conn.read(worksheet="Summary", ttl=0)
        existing_ids = df_existing['录入编号'].astype(str).tolist() if '录入编号' in df_existing.columns else []

        # 获取当前汇率
        rates = get_live_rates()

        new_rows = []
        detail_url = f"https://qyapi.weixin.qq.com/cgi-bin/oa/getapprovaldetail?access_token={token}"
        
        for sp_no in sp_nos:
            # 使用 WE-加后8位 作为录入编号去重
            uid = f"WE-{sp_no[-8:]}"
            if uid in existing_ids: continue
            
            det_res = requests.post(detail_url, json={"sp_no": sp_no}).json()
            if det_res.get("errcode") != 0: continue
            
            info = det_res.get("info", {})
            contents = info.get("apply_data", {}).get("contents", [])
            
            try:
                # --- 核心字段映射 (根据 CSV 逻辑) ---
                # contents[0]: 费用类型 (如 管理费)
                # contents[1]: 申请事由
                # contents[2]: 币种 (人民币/美元)
                # contents[3]: 金额 (数字)
                # contents[7]: 备注
                
                cat_type = contents[0]['value']['text']
                reason   = contents[1]['value']['text']
                currency = contents[2]['value']['text']
                raw_amt  = float(contents[3]['value']['new_number'])
                
                # 币种对齐
                final_curr = "CNY" if "人民币" in currency else "USD"
                
                # 计算折合美元
                exp_usd = round(raw_amt / rates.get(final_curr, 1.0), 2)
                
                # 时间处理：使用完成时间 (sp_finish_time)
                # 如果单据还没完成时间，用申请时间保底
                finish_ts = info.get('sp_finish_time', info.get('apply_time'))
                finish_dt = datetime.fromtimestamp(finish_ts).strftime('%Y-%m-%d %H:%M')

                new_rows.append({
                    "录入编号": uid,
                    "提交时间": finish_dt,  # ✅ 完成时间 对应 提交时间
                    "修改时间": "",
                    "摘要": reason,
                    "客户/项目信息": "企微同步",
                    "结算账户": "待分类",
                    "审批/发票单号": sp_no,  # ✅ 审批编号 对应 审批/发票单号
                    "资金性质": cat_type,
                    "实际金额": raw_amt,
                    "实际币种": final_curr,
                    "收入(USD)": 0.0,
                    "支出(USD)": exp_usd,
                    "余额(USD)": 0.0, # 稍后计算
                    "经手人": info.get("applyer", {}).get("name"),
                    "备注": contents[7]['value']['text'] if len(contents) > 7 else "来自企微同步"
                })
            except Exception:
                continue

        if new_rows:
            df_new = pd.DataFrame(new_rows)
            # 合并并重算余额
            df_final = pd.concat([df_existing, df_new], ignore_index=True)
            df_final = calculate_full_balance(df_final)
            
            # 更新云端
            conn.update(worksheet="Summary", data=df_final)
            # 更新版本号触发主界面刷新
            st.session_state.table_version += 1
            return f"✅ 成功从企微同步 {len(new_rows)} 条数据！"
            
        return "😴 云端已是最新，无新单据需要同步"
        
    except Exception as e:
        return f"❌ 出错了: {str(e)}"
@st.cache_data(ttl=300)
def load_data(version=0):
    try:
        # 使用 version 作为缓存键实现手动强刷，ttl=0 确保每次读取最新云端
        df = conn.read(worksheet="Summary", ttl=0)
        return df
    except Exception as e:
        st.error(f"数据加载失败: {e}")
        return pd.DataFrame()

# --- 3. 侧边栏 ---
with st.sidebar:
    st.title(f"💰 {L_MAIN['title_main']}")
    logout_text = {
        "zh": "🚪 退出登录",
        "en": "🚪 Logout",
        "km": "🚪 ចាកចេញ",
        "vi": "🚪 Đăng xuất"
    }.get(st.session_state.lang, "🚪 退出登录")
    
    if st.button(logout_text):
        st.session_state.logged_in = False
        st.rerun()
        
    st.divider()
    st.subheader("🤖 自动化助手")
    
    if st.button("🔄 同步企业微信数据", use_container_width=True):
        with st.spinner("正在从企微抓取数据..."):
            # 因为函数在 app.py 内部，直接调用即可
            result = sync_wecom_to_sheets(conn)
            
            if "✅" in result:
                st.success(result)
                st.rerun() # 同步成功后自动刷新页面显示新数据
            else:
                st.info(result)

# --- 4. 主页面数据加载 ---
df_main = load_data(version=st.session_state.table_version)

c_title, c_btn = st.columns([5, 2])
with c_title:
    st.header(L_MAIN["table_title"])
with c_btn:
    st.write("##") 
    if st.button(L_MAIN["btn_add"], use_container_width=True):
        # 传递 LOCAL_TZ 确保录入时间正确
        entry_dialog(conn, load_data, LOCAL_TZ)

# 处理弹窗调度
if st.session_state.get("show_edit_modal", False):
    edit_dialog(
        st.session_state.edit_target_id, 
        df_main, 
        conn, 
        LOCAL_TZ
    )

# --- 5. 数据预处理 (严谨处理：空值不回填) ---
if not df_main.empty:
    # 币种对齐，确保统计准确
    df_main['实际币种'] = df_main['实际币种'].replace(['RMB', '人民币'], 'CNY')
    
    # 辅助日期解析函数：仅用于看板统计，不影响原始数据显示
    def clean_date_for_stats(x):
        s = str(x).strip()
        if pd.isna(x) or s == "" or s.lower() == "nan":
            return pd.NaT # 重点：绝不填充当前时间，确保无数据的单据不参与统计
        try:
            dt = pd.to_datetime(s, errors='coerce')
            if pd.isna(dt): return pd.NaT
            return dt.replace(tzinfo=None) # 剥离时区以兼容筛选
        except:
            return pd.NaT

    # 生成隐藏辅助列，专供看板使用
    df_main['_calc_date'] = df_main['提交时间'].apply(clean_date_for_stats)

    # 数值列强制类型转换与清洗
    for col in ['收入(USD)', '支出(USD)', '余额(USD)', '实际金额']:
        if col in df_main.columns:
            df_main[col] = (
                df_main[col]
                .astype(str)
                .str.replace(r'[$,\s]', '', regex=True)
                .pipe(pd.to_numeric, errors='coerce')
                .fillna(0.0)
            )

# --- 6. 生成看板筛选列表 ---
current_now = datetime.now(LOCAL_TZ)
try:
    if not df_main.empty:
        valid_dates = df_main['_calc_date'].dropna()
        if not valid_dates.empty:
            year_list = sorted(valid_dates.dt.year.unique().tolist(), reverse=True)
        else:
            year_list = [current_now.year]
    else:
        year_list = [current_now.year]
except:
    year_list = [current_now.year]
    
month_list = list(range(1, 13))

# --- 7. 时间维度看板 ---
with st.container(border=True):
    st.markdown("#### 📅 时间维度看板") 
    c1, c2, c3 = st.columns([2, 2, 5]) 
    with c1:
        sel_year = st.selectbox("年份", year_list, index=0, label_visibility="collapsed")
    with c2:
        sel_month = st.selectbox("月份", month_list, index=current_now.month - 1, label_visibility="collapsed")
    
    # 筛选当前月份数据
    mask_this_month = (
        (df_main['_calc_date'].dt.year == int(sel_year)) & 
        (df_main['_calc_date'].dt.month == int(sel_month))
    )
    df_this_month = df_main[mask_this_month].copy()
    
    # 指标计算
    tm_inc = df_this_month['收入(USD)'].sum()
    tm_exp = df_this_month['支出(USD)'].sum()
    t_balance = df_main['收入(USD)'].sum() - df_main['支出(USD)'].sum()

    with c3:
        st.markdown(f"""
            <div style="margin-top: 7px; padding-left: 5px;">
                <span style="font-size: 1.2rem; font-weight: bold; color: #31333F;">
                    💡 当前统计周期：<span style="color: #4CAF50;">{sel_year}年{sel_month}月</span>
                </span>
            </div>
            """, unsafe_allow_html=True)
    # st.markdown("---")
    st.write("")
    
    m1, m2, m3 = st.columns(3)
    m1.metric(f"💰 {sel_month}月收入", f"${tm_inc:,.2f}")
    m2.metric(f"📉 {sel_month}月支出", f"${tm_exp:,.2f}")
    m3.metric("🏦 累计总结余", f"${t_balance:,.2f}")

# st.divider()
# 这里的 margin-top: -10px 会把分割线往上“提”，margin-bottom 控制下方间距
# st.markdown('<hr style="margin-top: 0px; margin-bottom: 10px; border: 0; border-top: 1px solid #ddd;">', unsafe_allow_html=True)

# --- 8. 各账户余额与支出排行 ---
col_l, col_r = st.columns([2, 1])
with col_l:
    # st.write("🏦 **各账户当前余额 (原币对账)**")
    st.markdown("##### 🏦 **各账户当前余额 (原币对账)**")
    if not df_main.empty:
        def calc_bank_balance(group):
            inc, exp, amt = group['收入(USD)'], group['支出(USD)'], group['实际金额']
            def get_raw_val(idx):
                val = amt.loc[idx]
                if val == 0 or pd.isna(val):
                    val = inc.loc[idx] if inc.loc[idx] > 0 else exp.loc[idx]
                return -val if exp.loc[idx] > 0 else val
            usd_bal = inc.sum() - exp.sum()
            raw_bal = sum(get_raw_val(idx) for idx in group.index)
            # 获取该账户最后一次使用的币种
            cur = group['实际币种'][group['实际币种'] != ""].iloc[-1] if not group['实际币种'].empty else "USD"
            return pd.Series([usd_bal, raw_bal, cur], index=['USD', 'RAW', 'CUR'])

        try:
            df_filtered = df_main[(df_main['结算账户'].notna()) & (df_main['结算账户'] != "") & (df_main['结算账户'] != "-- 请选择 --")].copy()
            if not df_filtered.empty:
                acc_stats = df_filtered.groupby('结算账户', group_keys=False).apply(calc_bank_balance).reset_index()
                
                # ✨ 从 logic 导入统一的 ISO_MAP
                from logic import ISO_MAP 
                acc_stats['原币种'] = acc_stats['CUR'].map(lambda x: ISO_MAP.get(x, x))
                
                # 重命名列名以便应用样式
                acc_display = acc_stats[['结算账户', 'RAW', '原币种', 'USD']].rename(columns={
                    "RAW": "原币余额",
                    "USD": "折合美元(USD)"
                })
                
                # ✨ 应用财务美化样式：千分符 + 2位小数 + 右对齐
                styled_acc = acc_display.style.format({
                    "原币余额": "{:,.2f}",
                    "折合美元(USD)": "{:,.2f}"
                })
                
                st.dataframe(
                    styled_acc, 
                    use_container_width=True, 
                    hide_index=True
                )
        except Exception as e:
            st.error(f"📊 余额计算异常: {e}")

with col_r:
    # st.write(f"🏷️ **{sel_month}月支出排行**")
    st.markdown(f"##### 🏷️ **{sel_month}月支出排行**")
    exp_stats = df_this_month[df_this_month['支出(USD)'] > 0].groupby('资金性质')[['支出(USD)']].sum().sort_values(by='支出(USD)', ascending=False).reset_index()
    if not exp_stats.empty:
        # ✨ 统一格式：千分符 + 2位小数 (去掉了之前可能的$符号，保持纯净右对齐)
        st.dataframe(
            exp_stats.style.format({"支出(USD)": "{:,.2f}"}), 
            use_container_width=True, 
            hide_index=True
        )
    else:
        st.caption("该月暂无支出记录")

# st.divider()
# 这里的 margin-top: -15px 会把分割线往上“提”，margin-bottom 控制下方间距
# st.markdown('<hr style="margin-top: 0px; margin-bottom: 10px; border: 0; border-top: 1px solid #ddd;">', unsafe_allow_html=True)

# --- 9. 流水明细表 ---
if not df_this_month.empty:
    # 💡 排除所有以 "_" 开头的辅助列（比如 _calc_date）
    display_cols = [c for c in df_main.columns if not str(c).startswith('_')] 
    
    # 倒序展示
    view_df = df_this_month[display_cols].copy().iloc[::-1]
    
    # 使用 .style.format 确保网页显示效果（千分符、右对齐）
    styled_df = view_df.style.format({
        "实际金额": "{:,.2f}",
        "收入(USD)": "{:,.2f}",
        "支出(USD)": "{:,.2f}",
        "余额(USD)": "{:,.2f}"
    })

    table_key = f"main_table_v_{st.session_state.table_version}"
    
    # --- 10. 一键导出Excel ---
    # 使用两列布局，第一列放标题，第二列放按钮
    title_col, btn_col = st.columns([5, 2])

    with title_col:
        # 动态标题：显示当前筛选的月份
        # st.subheader(f"📑 {sel_month}月流水明细")
        st.markdown(f"##### 📑 {sel_month}月流水明细")

    with btn_col:
        # 1. 初始化内存缓冲区
        excel_data = io.BytesIO()
        
        # 2. 使用 xlsxwriter 引擎创建 Excel 写入器
        with pd.ExcelWriter(excel_data, engine='xlsxwriter') as writer:
            view_df.to_excel(writer, index=False, sheet_name='流水明细')
            workbook  = writer.book
            worksheet = writer.sheets['流水明细']

            # 3. 定义基础格式 (宋体, 10号, 带边框)
            base_style = {'font_name': '宋体', 'font_size': 10, 'border': 1, 'valign': 'vcenter'}
            header_fmt = workbook.add_format({**base_style, 'bold': True, 'align': 'center', 'fg_color': '#1F4E78', 'font_color': 'white'})
            left_fmt = workbook.add_format({**base_style, 'align': 'left'})
            center_fmt = workbook.add_format({**base_style, 'align': 'center'})
            right_money_fmt = workbook.add_format({**base_style, 'align': 'right', 'num_format': '#,##0.00'})

            # 4. 遍历设置格式
            for col_idx, col_name in enumerate(view_df.columns):
                # 写入表头
                worksheet.write(0, col_idx, col_name, header_fmt)

                # 判断对齐方式
                if col_name in ["资金性质", "经手人"]:
                    target_fmt = center_fmt
                elif col_name in ["实际金额", "收入(USD)", "支出(USD)", "金额(USD)", "余额(USD)"]:
                    target_fmt = right_money_fmt
                else:
                    target_fmt = left_fmt

                # 自动计算列宽 (取内容长度和标题长度的最大值)
                max_len = max(view_df[col_name].astype(str).map(len).max(), len(str(col_name))) + 4
                worksheet.set_column(col_idx, col_idx, max_len, target_fmt)
                
            # ✨ --- 5. 打印与页面设置 --- ✨
            # A. 设置为 A4 纸 (9 代表 A4)
            worksheet.set_paper(9)
            
            # B. 设置纸张方向为横向 (1 = 纵向, 0 = 横向，xlsxwriter 默认为纵向)
            worksheet.set_landscape()
                
            # C. 设置页边距 (单位是英寸，1 英寸 ≈ 2.54 厘米)
            # 左右上下分别设为 0.5 英寸（约 1.27 厘米），这是一个比较平衡的留白
            worksheet.set_margins(left=0.5, right=0.5, top=0.5, bottom=0.5)
                
            # D. 设置自动缩放：将所有列调整在一页宽内打印
            worksheet.fit_to_pages(1, 0)
            
            # E. 页眉防伪
            # &[L]: 左侧内容, &[C]: 中间内容, &[R]: 右侧内容
            now_str = datetime.now().strftime('%Y-%m-%d %H:%M')
            header_text = f'&R&"宋体"&9打印于 {now_str}'
            worksheet.set_header(header_text)
        
            # F. 每一页都打印表头
            worksheet.repeat_rows(0)

        # 6. 渲染按钮
        st.download_button(
            label="📥 导出 Excel",
            data=excel_data.getvalue(),
            file_name=f"财务流水_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )

    # --- 11. 渲染表格 ---
    event = st.dataframe(
        styled_df,
        use_container_width=True,
        hide_index=True,
        on_select="rerun", 
        selection_mode="single-row",
        key=table_key
    )

    if event.selection.rows:
        selected_row_idx = event.selection.rows[0]
        # 确保只有在编辑弹窗没打开时，才打开操作弹窗，防止 API 冲突报错
        if not st.session_state.get('show_edit_modal', False):
            selected_row_data = view_df.iloc[selected_row_idx]
            st.session_state.current_active_id = selected_row_data.get("录入编号")
            # 弹出操作窗口
            row_action_dialog(selected_row_data, df_main, conn)
    else:
        # 如果没有任何行被选中，确保清理掉残留的 ID
        st.session_state.current_active_id = None
else:
    # 如果该月份没有数据，显示提示
    st.info(f"💡 {sel_year}年{sel_month}月暂无流水记录。")







