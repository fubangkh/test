import streamlit as st

def show_login_page():
    # 核心：使用 CSS 变量强制锁定全局底色，并穿透所有 BaseWeb 容器
    st.markdown("""
        <style>
        /* 1. 基础环境设置 */
        .stApp { background-color: #f8fafc !important; }
        .block-container { 
            max-width: 500px !important; 
            padding-top: 5rem !important; 
        }

        /* 2. 登录卡片 */
        div[data-testid="stVerticalBlockBorderWrapper"] {
            background-color: white !important;
            border-radius: 12px !important;
            box-shadow: 0 4px 20px rgba(0,0,0,0.05) !important;
            border: 1px solid #eef2f6 !important;
            padding: 2.5rem 2rem !important;
        }

        /* 3. 品牌标题区复刻 */
        .brand-header {
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 12px;
            margin-bottom: 5px;
        }
        .fb-logo {
            background-color: #1f7a3f;
            color: white;
            width: 44px;
            height: 44px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 800;
            font-size: 1.2rem;
            flex-shrink: 0;
        }
        .brand-text {
            color: #1f7a3f;
            font-size: 2.1rem;
            font-weight: 700;
            margin: 0;
            white-space: nowrap;
        }
        .brand-sub {
            text-align: center;
            color: #64748b;
            font-size: 0.9rem;
            margin-bottom: 25px;
        }

        /* 4. 深度修复：彻底消灭白色切块 (针对 BaseWeb 容器) */
        /* 强制覆盖 Streamlit 内部所有输入框相关的背景变量 */
        [data-testid="stTextInput"] {
            --style-bg: #f8fafc;
        }

        /* 穿透所有层级：外壳、中间层、内层、眼睛图标容器 */
        div[data-baseweb="input"], 
        div[data-baseweb="base-input"],
        div[role="presentation"],
        div[data-testid="stTextInput"] > div {
            background-color: #f8fafc !important;
            background: #f8fafc !important;
            border-radius: 8px !important;
        }

        /* 让 input 标签本身透明，确保看到的是底层的灰色 */
        div[data-testid="stTextInput"] input {
            background-color: transparent !important;
            border: none !important;
            height: 3rem !important;
            color: #1e293b !important;
        }

        /* 关键：修复右侧眼睛图标后的白色切块 */
        div[data-testid="stTextInput"] button,
        div[data-baseweb="input"] > div:last-child {
            background-color: transparent !important;
            background: transparent !important;
        }

        /* 输入框 Label */
        div[data-testid="stTextInput"] label {
            font-size: 0.95rem !important;
            color: #475569 !important;
            font-weight: 600 !important;
            margin-bottom: 6px !important;
        }

        /* 5. 立即登录按钮 */
        div.stButton > button {
            background-color: #1f7a3f !important;
            color: white !important;
            border-radius: 8px !important;
            height: 3.2rem !important;
            font-weight: 700 !important;
            border: none !important;
            margin-top: 15px;
            transition: 0.2s;
        }
        div.stButton > button:hover { background-color: #166534 !important; }

        .forgot-link { text-align: right; padding-top: 10px; color: #64748b; font-size: 13px; }
        </style>
    """, unsafe_allow_html=True)

    with st.container(border=True):
        st.markdown("""
            <div class="brand-header">
                <div class="fb-logo">FB</div>
                <h1 class="brand-text">富邦日记账</h1>
            </div>
            <p class="brand-sub">请输入管理员授权的凭证以继续</p>
        """, unsafe_allow_html=True)

        # 渲染输入框
        u = st.text_input("👤 账号", placeholder="请输入账号", key="user")
        p = st.text_input("🔒 密码", placeholder="请输入密码", type="password", key="pwd")

        c1, c2 = st.columns([1, 1])
        with c1:
            st.checkbox("记住我", value=True)
        with c2:
            st.markdown("<div class='forgot-link'>忘记密码？</div>", unsafe_allow_html=True)

        if st.button("立即登录", use_container_width=True):
            if u == "123" and p == "123":
                st.session_state.logged_in = True
                st.success("验证成功")
                st.rerun()
            else:
                st.error("❌ 账号或密码错误")

        st.markdown("""
            <hr style='margin: 20px 0; border:none; border-top:1px solid #f1f5f9;'>
            <div style='color: #94a3b8; font-size: 0.82rem; text-align: center;'>
                提示：这是示例页面，你可以将逻辑接入数据库。
            </div>
        """, unsafe_allow_html=True)
