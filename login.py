import streamlit as st

def show_login_page():
    primary_green = "#1f7a3f"
    primary_green_hover = "#166534"
    icon_gray = "#64748b"

    st.set_page_config(
        page_title="富邦日记账 - 登录",
        page_icon="🔐",
        layout="centered"
    )

    st.markdown(f"""
    <style>
    :root {{
        --primary: {primary_green};
        --primary-hover: {primary_green_hover};
        --icon: {icon_gray};
        --bg: #f8fafc;
        --card-border: rgba(15, 23, 42, 0.08);
        --shadow: 0 18px 48px rgba(15, 23, 42, 0.12);
        --radius: 30px;
        --inner-radius: 18px;
        --input-bg: #f1f5f9;
        --input-border: #e2e8f0;
    }}

    /* 始终显示滚动条，避免布局抖动 */
    html {{ overflow-y: scroll; }}

    .stApp {{
        background: var(--bg) !important;
    }}

    .block-container {{
        max-width: 560px !important;
        padding-top: 4.5rem !important;
        padding-bottom: 4rem !important;
    }}

    /* 卡片 */
    div[data-testid="stVerticalBlockBorderWrapper"] {{
        background:#fff !important;
        border:1px solid var(--card-border) !important;
        border-radius: var(--radius) !important;
        box-shadow: var(--shadow) !important;
        padding: 3rem 2.6rem 2.6rem 2.6rem !important;
    }}

    /* 内容同宽：输入/按钮/提示同宽 */
    .content-wrap {{
        width: 92%;
        margin: 0 auto;
    }}

    /* 标题区 */
    .brand-header {{
        display:flex;
        align-items:center;
        justify-content:center;
        gap:14px;
        margin-bottom: 10px;
    }}

    /* Logo 圆形 */
    .fb-logo {{
        width: 60px;
        height: 60px;
        border-radius: 9999px;
        display:flex;
        align-items:center;
        justify-content:center;
        background: var(--primary);
        color:#fff;
        font-weight: 900;
        font-size: 1.6rem;
        box-shadow: 0 10px 26px rgba(31, 122, 63, 0.25);
    }}

    .brand-text {{
        margin: 0;
        color: #0f172a;
        font-size: 2.2rem;
        font-weight: 900;
        letter-spacing: -1px;
        line-height: 1;
    }}

    .brand-sub {{
        text-align:center;
        color:#64748b;
        font-size:0.95rem;
        margin-bottom: 28px;
    }}

    /* label */
    .custom-label {{
        display:flex;
        align-items:center;
        gap: 8px;
        font-weight: 700;
        color: #334155;
        font-size: 0.95rem;
        margin-bottom: 8px;
    }}

    .custom-label svg {{
        width: 20px;
        height: 20px;
        stroke: var(--icon);
    }}

    /* =======================
       输入框统一（含密码眼睛）
       ======================= */

    /* 外壳 */
    div[data-baseweb="input"] > div {{
        background: var(--input-bg) !important;
        border: 1px solid var(--input-border) !important;
        border-radius: var(--inner-radius) !important;
        height: 3.3rem !important;
        display: flex !important;
        align-items: center !important;
        overflow: hidden !important;
    }}

    /* 输入文本 */
    div[data-baseweb="input"] input {{
        background: transparent !important;
        color: #0f172a !important;
        font-size: 14.5px !important;
        height: 3.3rem !important;
        line-height: 3.3rem !important;
        padding: 0 52px 0 14px !important; /* 右侧为眼睛预留 */
        border: none !important;
        outline: none !important;
    }}

    /* ✅ 关键：精准命中眼睛区域容器（第二个子 div）同背景 */
    div[data-baseweb="input"] > div > div:nth-child(2) {{
        background: var(--input-bg) !important;
        border-left: none !important;
        height: 3.3rem !important;
        display: flex !important;
        align-items: center !important;
        padding: 0 14px !important;
    }}

    /* 眼睛按钮：内部透明，避免叠色 */
    div[data-baseweb="input"] > div > div:nth-child(2) * {{
        background: transparent !important;
        box-shadow: none !important;
    }}

    div[data-baseweb="input"] button,
    div[data-baseweb="input"] [role="button"] {{
        background: transparent !important;
        border: none !important;
        box-shadow: none !important;
        outline: none !important;
        padding: 0 !important;
        margin: 0 !important;
    }}

    div[data-baseweb="input"] button:hover,
    div[data-baseweb="input"] button:active,
    div[data-baseweb="input"] button:focus,
    div[data-baseweb="input"] button:focus-visible {{
        background: transparent !important;
        box-shadow: none !important;
        outline: none !important;
    }}

    /* 图标颜色统一 */
    div[data-baseweb="input"] svg,
    div[data-baseweb="input"] svg path {{
        fill: var(--icon) !important;
        stroke: var(--icon) !important;
    }}

    /* 隐藏默认 label */
    div[data-testid="stTextInput"] label {{
        display:none !important;
    }}

    /* =======================
       登录按钮
       ======================= */
    .stButton > button {{
        width: 100% !important;
        height: 3.3rem !important;
        border-radius: var(--inner-radius) !important;
        border: none !important;
        background: var(--primary) !important;
        color: #fff !important;
        font-weight: 800 !important;
        font-size: 15px !important;
        margin-top: 12px;
        transition: all .15s ease-in-out;
    }}

    .stButton > button:hover {{
        background: var(--primary-hover) !important;
        transform: translateY(-1px);
    }}

    /* 提示区固定高度，避免跳动 */
    .msg-slot {{
        min-height: 78px;
        margin-top: 16px;
    }}

    .alert {{
        border-radius: var(--inner-radius);
        padding: 16px 18px;
        background: rgba(239, 68, 68, 0.10);
        border: 1px solid rgba(239, 68, 68, 0.2);
        color: #b91c1c;
        font-weight: 700;
    }}

    .divider {{
        margin: 22px 0;
        border:none;
        border-top:1px solid #f1f5f9;
    }}

    .footer-tip {{
        text-align:center;
        color:#94a3b8;
        font-size:0.85rem;
    }}
    </style>
    """, unsafe_allow_html=True)

    # SVG 图标（同风格同尺寸同色）
    user_svg = f"""
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"
         fill="none" stroke="{icon_gray}" stroke-width="2.5"
         stroke-linecap="round" stroke-linejoin="round">
      <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/>
      <circle cx="12" cy="7" r="4"/>
    </svg>
    """

    lock_svg = f"""
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"
         fill="none" stroke="{icon_gray}" stroke-width="2.5"
         stroke-linecap="round" stroke-linejoin="round">
      <rect x="3" y="11" width="18" height="11" rx="2"/>
      <path d="M7 11V7a5 5 0 0 1 10 0v4"/>
    </svg>
    """

    with st.container(border=True):
        st.markdown("""
            <div class="brand-header">
                <div class="fb-logo">FB</div>
                <h1 class="brand-text">富邦日记账</h1>
            </div>
            <div class="brand-sub">管理员授权登录</div>
        """, unsafe_allow_html=True)

        st.markdown('<div class="content-wrap">', unsafe_allow_html=True)

        st.markdown(f'<div class="custom-label">{user_svg}<span>账号</span></div>', unsafe_allow_html=True)
        u = st.text_input("账号", placeholder="请输入账号", key="user", label_visibility="collapsed")

        st.markdown(f'<div class="custom-label">{lock_svg}<span>密码</span></div>', unsafe_allow_html=True)
        p = st.text_input("密码", placeholder="请输入密码", type="password", key="pwd", label_visibility="collapsed")

        col1, col2 = st.columns([1, 1])
        with col1:
            st.checkbox("记住我", value=True)
        with col2:
            st.markdown(
                "<div style='text-align:right; padding-top:10px; color:#64748b; font-size:0.9rem;'>忘记密码？</div>",
                unsafe_allow_html=True
            )

        clicked = st.button("立即登录", use_container_width=True)

        msg_area = st.empty()
        msg_area.markdown('<div class="msg-slot"></div>', unsafe_allow_html=True)

        if clicked:
            if not u or not p:
                msg_area.markdown(
                    '<div class="msg-slot"><div class="alert">请先输入账号和密码</div></div>',
                    unsafe_allow_html=True
                )
            elif u == "123" and p == "123":
                st.success("登录成功")
            else:
                msg_area.markdown(
                    '<div class="msg-slot"><div class="alert">账号或密码错误</div></div>',
                    unsafe_allow_html=True
                )

        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<hr class="divider">', unsafe_allow_html=True)
        st.markdown('<div class="footer-tip">忘记密码请联系系统管理员</div>', unsafe_allow_html=True)


show_login_page()
