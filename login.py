import streamlit as st

def show_login_page():
    primary_green = "#1f7a3f"
    primary_green_hover = "#166534"
    icon_gray = "#64748b"

    st.set_page_config(page_title="富邦日记账 - 登录", page_icon="✅", layout="centered")

    # ====== CSS：解决 1)滚动条抖动 2)企业风格 3)圆形logo ======
    st.markdown(f"""
    <style>
    :root {{
        --primary: {primary_green};
        --primary-hover: {primary_green_hover};
        --icon: {icon_gray};
        --bg: #f8fafc;
        --card-border: rgba(15, 23, 42, 0.08);
        --shadow: 0 16px 40px rgba(15, 23, 42, 0.10);
        --radius: 24px;
    }}

    /* ✅ 关键：永远显示纵向滚动条，避免 st.error / st.success 触发页面左右抖动 */
    html {{
        overflow-y: scroll;
    }}

    .stApp {{
        background: var(--bg) !important;
    }}

    .block-container {{
        max-width: 520px !important;
        padding-top: 4.5rem !important;
        padding-bottom: 4rem !important;
    }}

    /* ✅ 用 container(border=True) 的外框做“卡片”，不再渲染空白 HTML 块 */
    div[data-testid="stVerticalBlockBorderWrapper"] {{
        background:#fff !important;
        border:1px solid var(--card-border) !important;
        border-radius: var(--radius) !important;
        box-shadow: var(--shadow) !important;
        padding: 2.6rem 2.4rem 2.2rem 2.4rem !important;
    }}

    /* 标题区：Logo + 标题同一行 */
    .brand-header {{
        display:flex;
        align-items:center;
        justify-content:center;
        gap:14px;
        margin-bottom: 10px;
    }}

    /* ✅ logo 圆形 */
    .fb-logo {{
        width: 56px;
        height: 56px;
        border-radius: 9999px;   /* 圆形 */
        display:flex;
        align-items:center;
        justify-content:center;
        background: var(--primary);
        color:#fff;
        font-weight: 900;
        font-size: 1.55rem;
        box-shadow: 0 10px 22px rgba(31, 122, 63, 0.25);
    }}

    .brand-text {{
        margin: 0;
        color: #0f172a;
        font-size: 2.1rem;
        font-weight: 900;
        letter-spacing: -0.8px;
        line-height: 1;
    }}

    .brand-sub {{
        text-align:center;
        color:#64748b;
        font-size:0.95rem;
        margin-bottom: 22px;
    }}

    /* 自定义 label（图标+文字） */
    .custom-label {{
        display:flex;
        align-items:center;
        gap: 8px;
        font-weight: 750;
        color: #334155;
        font-size: 0.95rem;
        margin: 0 0 8px 0;
    }}
    .custom-label svg {{
        width: 20px;
        height: 20px;
        stroke: var(--icon);
    }}

    /* 输入框 */
    div[data-baseweb="input"] > div {{
        border-radius: 12px !important;
        border: 1px solid #e2e8f0 !important;
        background: #f1f5f9 !important;
        height: 3.2rem !important;
    }}
    div[data-baseweb="input"] input {{
        background: transparent !important;
        color: #0f172a !important;
        font-size: 14.5px !important;
        height: 3.2rem !important;
        padding: 0 14px !important;
    }}

    /* 隐藏原生 label */
    div[data-testid="stTextInput"] label {{
        display:none !important;
    }}

    /* 按钮 */
    .stButton > button {{
        width: 100% !important;
        height: 3.2rem !important;
        border-radius: 12px !important;
        border: 1px solid rgba(31, 122, 63, 0.25) !important;
        background: var(--primary) !important;
        color: #fff !important;
        font-weight: 800 !important;
        font-size: 15px !important;
        margin-top: 10px;
        transition: all .15s ease-in-out;
    }}
    .stButton > button:hover {{
        background: var(--primary-hover) !important;
        transform: translateY(-1px);
    }}

    /* ✅ 固定高度消息槽：避免上下跳动 */
    .msg-slot {{
        min-height: 74px; /* 预留两行提示高度 */
        margin-top: 14px;
    }}

    /* ✅ 自定义错误提示（不用 st.error，避免 Streamlit 自己插入的 Alert 改 DOM） */
    .alert {{
        border-radius: 14px;
        padding: 16px 18px;
        border: 1px solid rgba(239, 68, 68, 0.18);
        background: rgba(239, 68, 68, 0.10);
        color: #b91c1c;
        font-weight: 700;
    }}

    .divider {{
        margin: 18px 0;
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

    # ====== SVG（同风格同尺寸同颜色）======
    user_svg = f"""
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"
         fill="none" stroke="{icon_gray}" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
      <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/>
      <circle cx="12" cy="7" r="4"/>
    </svg>
    """
    lock_svg = f"""
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"
         fill="none" stroke="{icon_gray}" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
      <rect x="3" y="11" width="18" height="11" rx="2" ry="2"/>
      <path d="M7 11V7a5 5 0 0 1 10 0v4"/>
    </svg>
    """

    # ====== 用 Streamlit 原生 container(border=True) 做卡片：不会出现“上方空白白框” ======
    with st.container(border=True):

        st.markdown("""
            <div class="brand-header">
                <div class="fb-logo">FB</div>
                <h1 class="brand-text">富邦日记账</h1>
            </div>
            <div class="brand-sub">管理员授权登录</div>
        """, unsafe_allow_html=True)

        st.markdown(f'<div class="custom-label">{user_svg}<span>账号</span></div>', unsafe_allow_html=True)
        u = st.text_input("账号", placeholder="请输入账号", key="user", label_visibility="collapsed")

        st.write("")

        st.markdown(f'<div class="custom-label">{lock_svg}<span>密码</span></div>', unsafe_allow_html=True)
        p = st.text_input("密码", placeholder="请输入密码", type="password", key="pwd", label_visibility="collapsed")

        c1, c2 = st.columns([1, 1])
        with c1:
            st.checkbox("记住我", value=True)
        with c2:
            st.markdown("<div style='text-align:right; padding-top:10px; color:#64748b; font-size:0.9rem;'>忘记密码？</div>",
                        unsafe_allow_html=True)

        clicked = st.button("立即登录", use_container_width=True)

        # ✅ 固定高度消息槽 + 自己渲染错误框（不再用 st.error）
        msg_area = st.empty()
        msg_area.markdown('<div class="msg-slot"></div>', unsafe_allow_html=True)

        if clicked:
            if (not u) or (not p):
                msg_area.markdown(
                    '<div class="msg-slot"><div class="alert">请先输入账号和密码</div></div>',
                    unsafe_allow_html=True
                )
            elif u == "123" and p == "123":
                st.session_state["logged_in"] = True
                # 这里你可以跳转页面
                st.rerun()
            else:
                msg_area.markdown(
                    '<div class="msg-slot"><div class="alert">账号或密码错误</div></div>',
                    unsafe_allow_html=True
                )

        st.markdown('<hr class="divider">', unsafe_allow_html=True)
        st.markdown('<div class="footer-tip">忘记密码请联系系统管理员</div>', unsafe_allow_html=True)
