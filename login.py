import streamlit as st

def show_login_page():
    # ========= 统一变量 =========
    primary_green = "#1f7a3f"
    primary_green_hover = "#166534"
    icon_gray = "#64748b"  # 统一图标颜色

    st.set_page_config(page_title="富邦日记账 - 登录", page_icon="✅", layout="centered")

    # ========= 企业级 UI 样式（精简 + 稳定选择器） =========
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

    /* 全局背景 + 容器宽度 */
    .stApp {{
        background: var(--bg) !important;
    }}
    .block-container {{
        max-width: 520px !important;
        padding-top: 4.5rem !important;
        padding-bottom: 4rem !important;
    }}

    /* 卡片（用我们自己的 wrapper，避免依赖 Streamlit 内部 testid 变化） */
    .login-card {{
        background: #fff;
        border: 1px solid var(--card-border);
        border-radius: var(--radius);
        box-shadow: var(--shadow);
        padding: 3rem 2.5rem 2.2rem 2.5rem;
    }}

    /* 标题区 */
    .brand-header {{
        display:flex;
        flex-direction:column;
        align-items:center;
        margin-bottom: 26px;
    }}
    .fb-logo {{
        width: 60px;
        height: 60px;
        border-radius: 18px;
        display:flex;
        align-items:center;
        justify-content:center;
        background: var(--primary);
        color: #fff;
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
        stroke: var(--icon);
    }}

    /* 输入框：用 BaseWeb input 的稳定结构选择器 */
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

    /* 隐藏 Streamlit 原生 label */
    label {{
        display: none !important;
    }}

    /* 按钮：统一宽度 + hover */
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

    /* 分割线 */
    .divider {{
        margin: 22px 0;
        border: none;
        border-top: 1px solid #f1f5f9;
    }}

    /* 底部提示 */
    .footer-tip {{
        text-align:center;
        color:#94a3b8;
        font-size:0.85rem;
    }}
    </style>
    """, unsafe_allow_html=True)

    # ========= SVG（同风格/同大小/同颜色） =========
    # 这套 SVG 采用 stroke 线条风格，视觉更像企业后台（类似 Lucide/Feather 风格）
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

    # ========= 页面内容 =========
    st.markdown('<div class="login-card">', unsafe_allow_html=True)

    st.markdown("""
        <div class="brand-header">
            <div class="fb-logo">FB</div>
            <h1 class="brand-text">富邦日记账</h1>
            <div class="brand-sub">管理员授权登录</div>
        </div>
    """, unsafe_allow_html=True)

    # 账号
    st.markdown(f'<div class="custom-label">{user_svg}<span>账号</span></div>', unsafe_allow_html=True)
    u = st.text_input("账号", placeholder="请输入账号", key="user", label_visibility="collapsed")

    st.write("")  # 间距

    # 密码
    st.markdown(f'<div class="custom-label">{lock_svg}<span>密码</span></div>', unsafe_allow_html=True)
    p = st.text_input("密码", placeholder="请输入密码", type="password", key="pwd", label_visibility="collapsed")

    # 辅助功能
    c1, c2 = st.columns([1, 1])
    with c1:
        st.checkbox("记住我", value=True)
    with c2:
        st.markdown(
            "<div style='text-align:right; padding-top:10px; color:#64748b; font-size:0.9rem;'>忘记密码？</div>",
            unsafe_allow_html=True
        )

    # 登录按钮
    if st.button("立即登录", use_container_width=True):
        if u == "123" and p == "123":
            st.session_state["logged_in"] = True
            st.rerun()
        else:
            st.error("账号或密码错误")

    st.markdown('<hr class="divider">', unsafe_allow_html=True)
    st.markdown('<div class="footer-tip">忘记密码请联系系统管理员</div>', unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)


# ====== 你在 app.py 里可以这样调用 ======
# show_login_page()
