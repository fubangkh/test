import streamlit as st

def show_login_page():
    # 使用最高优先级的 CSS 选择器锁定底色
    st.markdown("""
        <style>
        /* 1. 基础环境 */
        .stApp { background-color: #f8fafc !important; }
        .block-container { 
            max-width: 500px !important; 
            padding-top: 5rem !important; 
        }

        /* 2. 登录卡片容器 */
        div[data-testid="stVerticalBlockBorderWrapper"] {
            background-color: white !important;
            border-radius: 16px !important;
            box-shadow: 0 10px 25px rgba(0,0,0,0.04) !important;
            border: 1px solid #eef2f6 !important;
            padding: 2.5rem 2rem !important;
        }

        /* 3. 品牌标题区复刻 */
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

        /* 4. 重点修复：强制浅灰色底纹 */
        /* 定位到 Streamlit 输入框的最外层视觉容器 */
        div[data-testid="stTextInput"] > div[data-baseweb="input"] {
            background-color: #f1f5f9 !important; /* 稍微加深一点的浅灰色，更显质感 */
            border: 1px solid #e2e8f0 !important;
            border-radius: 10px !important;
        }

        /* 彻底杀掉内部所有可能变白的子容器背景 */
        div[data-testid="stTextInput"] div, 
        div[data-testid="stTextInput"] input,
        div[data-testid="stTextInput"] button,
        div[data-baseweb="base-input"] {
            background-color: transparent !important;
            background: transparent !important;
            border: none !important;
        }

        /* 输入框文字颜色 */
        div[data-testid="stTextInput"] input {
            color: #1e293b !important;
            height: 3.2rem !important;
            padding-left: 12px !important;
        }

        /* Label 与 辅助文案 */
        div[data-testid="stTextInput"] label {
            font-size: 0.95rem !important; color: #475569 !important;
            font-weight: 600 !important; margin-bottom: 8px !important;
        }

        /* 5. 立即登录按钮 */
        div.stButton > button {
            background-color: #1f7a3f !important; color: white !important;
            border-radius: 10px !important; height: 3.4rem !important;
            font-weight: 700 !important; border: none !important;
            margin-top: 15px; transition: 0.2s ease;
        }
        div.stButton > button:hover { background-color: #166534 !important; transform: translateY(-1px); }

        .forgot-link { text-align: right; padding-top: 10px; color: #64748b; font-size: 13px; }
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

        if st.button("立即登录", use_container_width=True):
            if u == "123" and p == "123":
                st.session_state.logged_in = True
                st.success("验证成功")
                st.rerun()
            else:
                st.error("❌ 账号或密码错误")

        st.markdown("""
            <hr style='margin: 25px 0; border:none; border-top:1px solid #f1f5f9;'>
            <p style='color: #94a3b8; font-size: 0.82rem; text-align: center;'>
                提示：这是示例页面，您可以将逻辑接入数据库。
            </p>
        """, unsafe_allow_html=True)
