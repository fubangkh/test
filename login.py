import streamlit as st

def show_login_page():
    # 1. 定义灰色 SVG 图标 (经过 URL 编码，确保 CSS 能识别)
    # 颜色统一使用灰色 #64748b，粗细统一为 2.5
    user_icon = "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='24' height='24' viewBox='0 0 24 24' fill='none' stroke='%2364748b' stroke-width='2.5' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2'/%3E%3Ccircle cx='12' cy='7' r='4'/%3E%3C/svg%3E"
    lock_icon = "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='24' height='24' viewBox='0 0 24 24' fill='none' stroke='%2364748b' stroke-width='2.5' stroke-linecap='round' stroke-linejoin='round'%3E%3Crect x='3' y='11' width='18' height='11' rx='2' ry='2'/%3E%3Cpath d='M7 11V7a5 5 0 0 1 10 0v4'/%3E%3C/svg%3E"

    st.markdown(f"""
        <style>
        /* 全局背景 */
        .stApp {{ background-color: #f8fafc !important; }}
        .block-container {{ max-width: 480px !important; padding-top: 5rem !important; }}

        /* 登录卡片：超大圆角 */
        div[data-testid="stVerticalBlockBorderWrapper"] {{
            background-color: white !important;
            border-radius: 28px !important; 
            box-shadow: 0 20px 40px rgba(0, 0, 0, 0.06) !important;
            border: 1px solid #f1f5f9 !important;
            padding: 3rem 2rem !important;
        }}

        /* 标题样式优化 */
        .brand-text {{ 
            color: #166534 !important; 
            font-size: 2.4rem !important; 
            font-weight: 800 !important; 
            text-align: center;
            margin-bottom: 5px;
        }}
        .brand-sub {{ text-align: center; color: #64748b; margin-bottom: 30px; font-size: 0.95rem; }}

        /* --- 核心：将图标注入输入框内部 --- */
        div[data-testid="stTextInput"] input {{
            background-color: #f1f5f9 !important;
            border: 1px solid #e2e8f0 !important;
            border-radius: 14px !important;
            height: 3.2rem !important;
            padding-left: 3rem !important; /* 为左侧图标留出空间 */
            background-repeat: no-repeat !important;
            background-position: 1rem center !important; /* 图标居中对齐 */
            background-size: 1.2rem !important;
            transition: all 0.2s;
        }}

        /* 分别给账号和密码框注入不同的 SVG */
        div[data-testid="stTextInput"]:nth-of-type(1) input {{
            background-image: url("{user_icon}") !important;
        }}
        div[data-testid="stTextInput"]:nth-of-type(2) input {{
            background-image: url("{lock_icon}") !important;
        }}

        /* 统一 Label 样式 */
        div[data-testid="stTextInput"] label {{
            font-weight: 700 !important;
            color: #334155 !important;
            margin-left: 5px !important;
            margin-bottom: 8px !important;
        }}

        /* 按钮对齐与圆角 */
        div.stButton > button {{
            background-color: #1f7a3f !important;
            color: white !important;
            border-radius: 14px !important;
            height: 3.2rem !important;
            width: 100% !important;
            font-weight: 700 !important;
            border: none !important;
            margin-top: 15px;
        }}

        /* 提示框对齐 */
        div[data-testid="stNotification"] {{ border-radius: 14px !important; }}
        </style>
    """, unsafe_allow_html=True)

    with st.container():
        # 顶部徽章
        st.markdown("""
            <div style='display: flex; justify-content: center; margin-bottom: 15px;'>
                <div style='background: #1f7a3f; color: white; width: 56px; height: 56px; border-radius: 16px; display: flex; align-items: center; justify-content: center; font-weight: 800; font-size: 1.4rem; box-shadow: 0 8px 16px rgba(31,122,63,0.2);'>FB</div>
            </div>
            <div class="brand-text">富邦日记账</div>
            <div class="brand-sub">欢迎使用管理员授权系统</div>
        """, unsafe_allow_html=True)

        # 输入组件 (现在图标在框内，看起来非常稳)
        u = st.text_input("账号", placeholder="请输入您的账号", key="user")
        p = st.text_input("密码", placeholder="请输入您的密码", type="password", key="pwd")

        # 辅助功能
        c1, c2 = st.columns([1, 1])
        with c1: st.checkbox("记住我", value=True)
        with c2: st.markdown("<div style='text-align:right; padding-top:10px; color:#64748b; font-size:0.9rem;'>忘记密码？</div>", unsafe_allow_html=True)

        if st.button("立即登录", use_container_width=True):
            if u == "123" and p == "123":
                st.success("登录成功")
                st.rerun()
            else:
                st.error("账号或密码错误")

        st.markdown("<hr style='margin: 25px 0; border:none; border-top:1px solid #f1f5f9;'>", unsafe_allow_html=True)
        st.markdown("<div style='text-align:center; color:#94a3b8; font-size:0.85rem;'>💡 忘记密码请联系系统管理员</div>", unsafe_allow_html=True)
