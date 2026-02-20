import streamlit as st

def show_login_page():
    primary_green = "#1f7a3f"
    primary_green_hover = "#166534"
    icon_gray = "#64748b"

    st.set_page_config(page_title="富邦日记账 - 登录", page_icon="✅", layout="centered")

    st.markdown(f"""
    <style>
    :root {{
        --primary: {primary_green};
        --primary-hover: {primary_green_hover};
        --icon: {icon_gray};
        --bg: #f8fafc;
        --card-border: rgba(15, 23, 42, 0.08);
        --shadow: 0 16px 40px rgba(15, 23, 42, 0.10);
        --radius: 30px;              /* ✅ 1) 卡片圆角更大 */
        --inner-radius: 16px;        /* 输入框/按钮圆角 */
        --content-width: 85%;        /* ✅ 2) 统一内容宽度（输入/按钮/提示） */
    }}

    html {{ overflow-y: scroll; }}
    .stApp {{ background: var(--bg) !important; }}
    .block-container {{
        max-width: 560px !important;
        padding-top: 4.2rem !important;
        padding-bottom: 4rem !important;
    }}

    /* 卡片 */
    div[data-testid="stVerticalBlockBorderWrapper"] {{
        background:#fff !important;
        border:1px solid var(--card-border) !important;
        border-radius: var(--radius) !important;
        box-shadow: var(--shadow) !important;
        padding: 2.6rem 2.4rem 2.2rem 2.4rem !important;
    }}

    /* ✅ 统一内容宽度容器：让输入框/按钮/提示“同宽” */
    .content-wrap {{
        width: var(--content-width);
        margin: 0 auto;   /* 居中 */
    }}

    /* 标题 */
    .brand-header {{
        display:flex;
        align-items:center;
        justify-content:center;
        gap:14px;
        margin-bottom: 10px;
    }}
    .fb-logo {{
        width: 56px; height: 56px;
        border-radius: 9999px;
        display:flex; align-items:center; justify-content:center;
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

    /* label */
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

    /* ✅ 3) 输入框文字垂直居中：用 line-height + padding 修正 */
    div[data-baseweb="input"] > div {{
        border-radius: var(--inner-radius) !important;
        border: 1px solid #e2e8f0 !important;
        background: #f1f5f9 !important;
        height: 3.2rem !important;
        display: flex !important;
        align-items: center !important;
    }}
    div[data-baseweb="input"] input {{
        background: transparent !important;
        color: #0f172a !important;
        font-size: 14.5px !important;
        height: 3.2rem !important;
        line-height: 3.2rem !important;  /* ✅ 垂直居中关键 */
        padding: 0 14px !important;
    }}

    div[data-testid="stTextInput"] label {{
        display:none !important;
    }}

    /* ✅ 按钮同宽：不再 100%，跟 content-wrap 宽度走 */
    .stButton > button {{
        width: 100% !important;
        height: 3.2rem !important;
        border-radius: var(--inner-radius) !important;
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

    /* 消息槽 + 错误提示（同宽） */
    .msg-slot {{
        min-height: 74px;
        margin-top: 14px;
    }}
    .alert {{
        width: 100%;
        border-radius: var(--inner-radius);
        padding: 16px 18px;
        border: 1px solid rgba(239, 68, 68, 0.18);
        background: rgba(239, 68, 68, 0.10);
        color: #b91c1c;
        font-weight: 700;
        box-sizing: border-box;
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

    with st.container(border=True):
        st.markdown("""
            <div class="brand-header">
                <div class="fb-logo">FB</div>
                <h1 class="brand-text">富邦日记账</h1>
            </div>
            <div class="brand-sub">管理员授权登录</div>
        """, unsafe_allow_html=True)

        # ✅ 内容统一宽度开始
        st.markdown('<div class="content-wrap">', unsafe_allow_html=True)

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
                st.rerun()
            else:
                msg_area.markdown(
                    '<div class="msg-slot"><div class="alert">账号或密码错误</div></div>',
                    unsafe_allow_html=True
                )

        st.markdown('</div>', unsafe_allow_html=True)
        # ✅ 内容统一宽度结束

        st.markdown('<hr class="divider">', unsafe_allow_html=True)
        st.markdown('<div class="footer-tip">忘记密码请联系系统管理员</div>', unsafe_allow_html=True)
