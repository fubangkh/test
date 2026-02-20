import streamlit as st

def show_login_page():
    # 深度样式定制：对齐所有组件宽度与圆角
    st.markdown("""
        <style>
        /* 1. 全局背景与容器 */
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
            padding: 2.5rem 2rem !important;
        }

        /* 3. 品牌标题区 */
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

        /* 4. 输入框锁定 (宽度控制核心) */
        div[data-testid="stTextInput"] > div[data-baseweb="input"] {
            background-color: #f1f5f9 !important;
            border: 1px solid #e2e8f0 !important;
            border-radius: 10px !important; /* 统一圆角基准 */
        }

        /* 解决文字上下居中问题 */
        div[data-testid="stTextInput"] input {
            color: #1e293b !important;
            height: 2.8rem !important; /* 与按钮高度呼应 */
            padding: 0 12px !important;
            display: flex !important;
            align-items: center !important;
            background-color: transparent !important;
            border: none !important;
        }

        /* 消除密码框眼睛图标的干扰 */
        div[data-testid="stTextInput"] button {
            background-color: transparent !important;
            border: none !important;
        }

        /* 5. 立即登录按钮 (宽度对齐与圆角) */
        div.stButton > button {
            background-color: #1f7a3f !important;
            color: white !important;
            border-radius: 10px !important; /* 圆角与输入框一致 */
            height: 2.8rem !important;
            width: 100% !important; /* 强制填满容器宽度 */
            font-weight: 700 !important;
            border: none !important;
            margin-top: 5px;
            transition: 0.2s ease;
        }

        /* 6. 错误提示框样式 (宽度与圆角同步) */
        div[data-testid="stNotification"] {
            border-radius: 10px !important; /* 圆角一致 */
            border: none !important;
            padding: 0.5rem 1rem !important;
        }

        /* 忘记密码与记住我对齐 */
        .forgot-link { text-align: right; padding-top: 10px; color: #64748b; font-size: 13px; }
        
        /* 底部提示区样式 */
        .footer-tip {
            display: flex; align-items: center; justify-content: center;
            gap: 8px; color: #64748b; font-size: 0.9rem;
            margin-top: 25px;
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

        # 渲染输入框
        u = st.text_input("👤 账号", placeholder="请输入账号", key="user")
        p = st.text_input("🔒 密码", placeholder="请输入密码", type="password", key="pwd")

        c1, c2 = st.columns([1, 1])
        with c1:
            st.checkbox("记住我", value=True)
        with c2:
            st.markdown("<div class='forgot-link'>忘记密码？</div>", unsafe_allow_html=True)

        # 登录验证逻辑
        if st.button("立即登录", use_container_width=True):
            if u == "123" and p == "123":
                st.session_state.logged_in = True
                st.success("验证成功")
                st.rerun()
            else:
                st.error("账号或密码错误")

        # 底部提示：找回之前的黄色小图标
        st.markdown("<hr style='margin: 20px 0; border:none; border-top:1px solid #f1f5f9;'>", unsafe_allow_html=True)
        st.markdown("""
            <div class="footer-tip">
                <span>💡</span> 忘记密码请联系系统管理员
            </div>
        """, unsafe_allow_html=True)
