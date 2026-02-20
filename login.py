import streamlit as st

def show_login_page():
    # 深度样式定制
    st.markdown("""
        <style>
        .stApp { background-color: #f8fafc !important; }
        .block-container { 
            max-width: 500px !important; 
            padding-top: 5rem !important; 
        }

        /* 外框：大气圆角 */
        div[data-testid="stVerticalBlockBorderWrapper"] {
            background-color: white !important;
            border-radius: 24px !important; 
            box-shadow: 0 15px 35px rgba(0, 0, 0, 0.05) !important;
            border: 1px solid #eef2f6 !important;
            padding: 3rem 2.5rem !important;
        }

        /* FB Logo 徽章 */
        .brand-header {
            display: flex; flex-direction: column; align-items: center;
            margin-bottom: 30px;
        }
        .fb-logo {
            background-color: #1f7a3f;
            color: white;
            width: 60px; height: 60px;
            border-radius: 18px;
            display: flex; align-items: center; justify-content: center;
            font-weight: 800; font-size: 1.6rem;
            box-shadow: 0 6px 15px rgba(31, 122, 63, 0.25);
            margin-bottom: 15px;
        }
        .brand-text {
            color: #064e3b; /* 森林深绿 */
            font-size: 2.2rem;
            font-weight: 800;
            letter-spacing: -1px;
            margin: 0;
        }

        /* 输入框底色与垂直居中 */
        div[data-testid="stTextInput"] > div[data-baseweb="input"] {
            background-color: #f1f5f9 !important;
            border: 1px solid #e2e8f0 !important;
            border-radius: 12px !important;
        }

        div[data-testid="stTextInput"] input {
            color: #1e293b !important;
            background-color: transparent !important;
            height: 3.2rem !important;
            line-height: 3.2rem !important;
            padding: 0 15px !important;
            display: flex !important;
            align-items: center !important;
            font-size: 1rem !important;
        }

        /* 登录按钮 */
        div.stButton > button {
            background-color: #1f7a3f !important;
            color: white !important;
            border-radius: 12px !important;
            height: 3.2rem !important;
            width: 100% !important;
            font-weight: 700 !important;
            border: none !important;
            margin-top: 10px;
            box-shadow: 0 4px 12px rgba(31, 122, 63, 0.2);
        }

        /* 标签加粗 */
        div[data-testid="stTextInput"] label {
            font-weight: 700 !important;
            color: #334155 !important;
            margin-bottom: 8px !important;
            font-size: 0.95rem !important;
        }
        </style>
    """, unsafe_allow_html=True)

    with st.container(border=True):
        st.markdown("""
            <div class="brand-header">
                <div class="fb-logo">FB</div>
                <h1 class="brand-text">富邦日记账</h1>
                <p style='color: #64748b; margin-top: 8px; font-size: 0.95rem;'>管理员授权登录</p>
            </div>
        """, unsafe_allow_html=True)

        # 这里换成了视觉上更饱满的图标
        u = st.text_input("👤 账号", placeholder="请输入账号", key="user")
        p = st.text_input("🔐 密码", placeholder="请输入密码", type="password", key="pwd")

        c1, c2 = st.columns([1, 1])
        with c1:
            st.checkbox("记住我", value=True)
        with c2:
            st.markdown("<div style='text-align:right; padding-top:10px; color:#64748b; font-size:0.9rem;'>忘记密码？</div>", unsafe_allow_html=True)

        if st.button("立即登录", use_container_width=True):
            if u == "123" and p == "123":
                st.session_state.logged_in = True
                st.success("验证成功")
                st.rerun()
            else:
                st.error("账号或密码错误")

        st.markdown("<hr style='margin: 25px 0; border:none; border-top:1px solid #f1f5f9;'>", unsafe_allow_html=True)
        st.markdown("<div style='text-align:center; color:#94a3b8; font-size:0.85rem;'>💡 忘记密码请联系系统管理员</div>", unsafe_allow_html=True)
