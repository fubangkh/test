import streamlit as st

def show_login_page():
    primary_green = "#1f7a3f"
    primary_green_hover = "#166534"
    icon_gray = "#64748b"

    st.set_page_config(page_title="富邦日记账 - 登录", page_icon="✅", layout="centered")

    st.markdown(f"""
    <style>
    .stApp {{
        background: #f8fafc !important;
    }}
    .block-container {{
        max-width: 520px !important;
        padding-top: 4.5rem !important;
        padding-bottom: 4rem !important;
    }}

    /* ✅ 关键：把“卡片样式”打到 Streamlit 容器外框上 */
    div[data-testid="stVerticalBlockBorderWrapper"] {{
        background: #fff !important;
        border: 1px solid rgba(15, 23, 42, 0.08) !important;
        border-radius: 24px !important;
        box-shadow: 0 16px 40px rgba(15, 23, 42, 0.10) !important;
        padding: 3rem 2.5rem 2.2rem 2.5rem !important;
    }}

    /* 标题区 */
    .brand-header {{
        display:flex;
        flex-direction:column;
        align-items:center;
        margin-bottom: 26px;
    }}
    .fb-logo {{
        width: 60px; height: 60px;
        border-radius: 18px;
        display:flex; align-items:center; justify-content:center;
        background: {primary_green};
        color:#fff;
        font-weight: 900;
        font-size: 1.6rem;
        box-shadow: 0 10px 22px rgba(31, 122, 63, 0.25);
        margin-bottom: 14px;
    }}
    .brand-text {{
        margin: 0;
        color: #064e3b;
        font-size: 2.1rem;
        font-weight: 900;
        letter-spacing: -0.8px;
    }}
    .brand-sub {{
        margin-top: 8px;
        color: #64748b;
        font-size: 0.95rem;
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
        stroke: {icon_gray};
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

    /* 隐藏原生 label（只隐藏 text_input 的 label，避免误伤其它） */
    div[data-testid="stTextInput"] label {{
        display: none !important;
    }}

    /* 按钮 */
    .stButton > button {{
        width: 100% !important;
        height: 3.2rem !important;
        border-radius: 12px !important;
        border: 1px solid rgba(31, 122, 63, 0.25) !important;
        background: {primary_green} !important;
        color: #fff !important;
        font-weight: 800 !important;
        font-size: 15px !important;
        margin-top: 10px;
        transition: all .15s ease-in-out;
    }}
    .stButton > button:hover {{
        background: {primary_green_hover} !important;
        transform: translateY(-1px);
    }}
    </style>
    """, unsafe_allow_html=True)

    # SVG（同色系同尺寸同风格）
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

    # ✅ 关键：所有内容放到同一个 container 里，让 wrapper 变卡片
    with st.container():
        st.markdown("""
            <div class="brand-header">
                <div class="fb-logo">FB</div>
                <h1 class="brand-text">富邦日记账</h1>
                <div class="brand-sub">管理员授权登录</div>
            </div>
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

        if st.button("立即登录", use_container_width=True):
            if u == "123" and p == "123":
                st.session_state["logged_in"] = True
                st.rerun()
            else:
                st.error("账号或密码错误")

        st.markdown("<hr style='margin: 22px 0; border:none; border-top:1px solid #f1f5f9;'>", unsafe_allow_html=True)
        st.markdown("<div style='text-align:center; color:#94a3b8; font-size:0.85rem;'>忘记密码请联系系统管理员</div>",
                    unsafe_allow_html=True)
