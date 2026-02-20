import streamlit as st

def show_login_page():
    # 1. 深度 CSS 覆盖：锁定所有输入组件的底色
    st.markdown("""
        <style>
        /* 全局背景与容器 */
        .stApp { background-color: #f8fafc !important; }
        .block-container { 
            max-width: 520px !important; 
            padding-top: 5rem !important; 
        }

        /* 登录卡片 */
        div[data-testid="stVerticalBlockBorderWrapper"] {
            background-color: white !important;
            border-radius: 12px !important;
            box-shadow: 0 4px 20px rgba(0,0,0,0.05) !important;
            border: 1px solid #eef2f6 !important;
            padding: 2.5rem 1.8rem !important;
        }

        /* 标题区：FB徽章 + 文字 */
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
            font-size: 2.2rem;
            font-weight: 700;
            margin: 0;
            white-space: nowrap;
        }
        .brand-sub {
            text-align: center;
            color: #64748b;
            font-size: 0.95rem;
            margin-bottom: 30px;
        }

        /* --- 核心修复：深度锁定底色 --- */
        /* 1. 覆盖外层容器 */
        div[data-baseweb="input"] {
            background-color: #f8fafc !important;
            border-radius: 8px !important;
            border: 1px solid #e2e8f0 !important;
        }
        
        /* 2. 覆盖内层输入框（包括账号框和密码框） */
        div[data-testid="stTextInput"] input {
            background-color: transparent !important; /* 让底色透出来 */
            border: none !important;
            height: 3rem !important;
        }

        /* 3. 针对账号框特别强制（防止它变白） */
        div[data-testid="stTextInput"] div[data-baseweb="input"] {
            background-color: #f8fafc !important;
        }

        /* 4. 隐藏原生 Label 并美化自定义 Label */
        div[data-testid="stTextInput"] label {
            font-size: 0.95rem !important;
            color: #475569 !important;
            font-weight: 600 !important;
            margin-bottom: 8px !important;
        }

        /* 按钮与其它 */
        div.stButton > button {
            background-color: #1f7a3f !important;
            color: white !important;
            border-radius: 8px !important;
            height: 3.2rem !important;
            font-weight: 700 !important;
            border: none !important;
            margin-top: 15px;
        }
        div.stButton > button:hover { background-color: #166534 !important; }
        .forgot-link { text-align: right; padding-top: 15px; color: #64748b; font-size: 13px; }
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

        # 输入组件
        username = st.text_input("👤 账号", placeholder="请输入账号", key="user")
        password = st.text_input("🔒 密码", placeholder="请输入密码", type="password", key="pwd")

        c1, c2 = st.columns([1, 1])
        with c1:
            st.checkbox("记住我", value=True)
        with c2:
            st.markdown("<div class='forgot-link'>忘记密码？</div>", unsafe_allow_html=True)

        if st.button("立即登录", use_container_width=True):
            if username == "123" and password == "123":
                st.session_state.logged_in = True
                st.success("验证成功")
                st.rerun()
            else:
                st.error("❌ 账号或密码错误")

        st.markdown("""
            <hr style='margin: 25px 0; border:none; border-top:1px solid #f1f5f9;'>
            <div style='color: #94a3b8; font-size: 0.85rem;'>
                提示：这是示例页面，你可以把认证逻辑接到数据库 / API / OAuth。
            </div>
        """, unsafe_allow_html=True)
