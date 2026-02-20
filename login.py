import streamlit as st

def show_login_page():
    st.markdown("""
        <style>
        /* 1. 环境与容器控制 */
        .stApp { background-color: #f8fafc !important; }
        .block-container { 
            max-width: 500px !important; 
            padding-top: 5rem !important; 
        }

        /* 2. 登录卡片 */
        div[data-testid="stVerticalBlockBorderWrapper"] {
            background-color: white !important;
            border-radius: 16px !important;
            box-shadow: 0 10px 25px rgba(0,0,0,0.04) !important;
            border: 1px solid #eef2f6 !important;
            padding: 2.5rem 2.2rem !important; /* 微调内边距确保内部宽度一致 */
        }

        /* 3. 标题区 */
        .brand-header {
            display: flex; align-items: center; justify-content: center;
            gap: 12px; margin-bottom: 5px;
        }
        .fb-logo {
            background-color: #1f7a3f; color: white;
            width: 44px; height: 44px; border-radius: 50%;
            display: flex; align-items: center; justify-content: center;
            font-weight: 800; font-size: 1.2rem; flex-shrink: 0;
        }
        .brand-text {
            color: #1f7a3f; font-size: 2.1rem; font-weight: 700;
            margin: 0; white-space: nowrap;
        }

        /* 4. 输入框深度锁定 & 文字居中修复 */
        div[data-testid="stTextInput"] > div[data-baseweb="input"] {
            background-color: #f1f5f9 !important;
            border: 1px solid #e2e8f0 !important;
            border-radius: 10px !important;
            height: 3rem !important; /* 固定容器高度 */
        }

        div[data-testid="stTextInput"] input {
            color: #1e293b !important;
            background-color: transparent !important;
            border: none !important;
            /* --- 核心修复：文字垂直居中 --- */
            height: 3rem !important;
            line-height: 3rem !important; 
            padding: 0 12px !important;
            display: flex !important;
            align-items: center !important;
        }

        /* 5. 按钮：宽度对齐 & 比例 */
        div.stButton > button {
            background-color: #1f7a3f !important;
            color: white !important;
            border-radius: 10px !important;
            height: 3rem !important; /* 与输入框高度保持一致更协调 */
            width: 100% !important;
            font-weight: 700 !important;
            border: none !important;
            margin-top: 5px;
        }

        /* 6. 重点：错误提示框宽度缩减 */
        /* 强制覆盖 st.error 的容器宽度，使其与输入框边缘完全重合 */
        div[data-testid="stNotification"] {
            border-radius: 10px !important;
            margin: 10px 0 !important;
            width: 100% !important;
            max-width: 100% !important;
        }
        /* 针对内层布局做对齐补偿 */
        div[data-testid="stNotification"] > div {
            padding: 0.6rem 1rem !important;
        }

        /* 忘记密码与底部提示 */
        .forgot-link { text-align: right; padding-top: 10px; color: #64748b; font-size: 13px; }
        .footer-tip {
            display: flex; align-items: center; justify-content: center;
            gap: 8px; color: #64748b; font-size: 0.9rem; margin-top: 25px;
        }
        </style>
    """, unsafe_allow_html=True)

    with st.container(border=True):
        st.markdown("""
            <div class="brand-header">
                <div class="fb-logo">FB</div>
                <h1 class="brand-text">富邦日记账</h1>
            </div>
            <p style='text-align: center; color: #64748b; font-size: 0.9rem; margin-bottom: 25px;'>
                请输入管理员授权的凭证以继续
            </p>
        """, unsafe_allow_html=True)

        u = st.text_input("👤 账号", placeholder="请输入账号", key="user")
        p = st.text_input("🔒 密码", placeholder="请输入密码", type="password", key="pwd")

        c1, c2 = st.columns([1, 1])
        with c1:
            st.checkbox("记住我", value=True)
        with c2:
            st.markdown("<div class='forgot-link'>忘记密码？</div>", unsafe_allow_html=True)

        # 验证逻辑
        if st.button("立即登录", use_container_width=True):
            if u == "123" and p == "123":
                st.session_state.logged_in = True
                st.success("验证成功")
                st.rerun()
            else:
                # 错误提示：文字更简洁
                st.error("账号或密码错误")

        st.markdown("<hr style='margin: 20px 0; border:none; border-top:1px solid #f1f5f9;'>", unsafe_allow_html=True)
        st.markdown("""
            <div class="footer-tip">
                <span>💡</span> 忘记密码请联系系统管理员
            </div>
        """, unsafe_allow_html=True)
