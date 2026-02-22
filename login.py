import streamlit as st

def show_login_page():
    # --- 1. 多语言字典 ---
    LANG_DICT = {
        "zh": {
            "title": "富邦日记账",
            "user_label": "账号",
            "user_placeholder": "请输入账号，测试账号123",
            "pwd_label": "密码",
            "pwd_placeholder": "请输入密码，测试密码123",
            "remember": "记住我",
            "login_btn": "立即登录",
            "err_empty": "⚠️ 请先输入账号和密码",
            "err_wrong": "⚠️ 账号或密码不正确"
        },
        "en": {
            "title": "Fubang Ledger",
            "user_label": "Account",
            "user_placeholder": "Enter account, test: 123",
            "pwd_label": "Password",
            "pwd_placeholder": "Enter password, test: 123",
            "remember": "Remember Me",
            "login_btn": "Sign In",
            "err_empty": "⚠️ Please enter account and password",
            "err_wrong": "⚠️ Invalid account or password"
        }
    }

    # 初始化语言
    if 'lang' not in st.session_state:
        st.session_state.lang = "zh"

    # 回调函数：选完立即重绘
    def on_lang_change():
        st.session_state.lang = "zh" if st.session_state.lang_sel == "CN" else "en"

    L = LANG_DICT[st.session_state.lang]

    # 图标
    user_svg = "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='18' height='18' viewBox='0 0 24 24' fill='none' stroke='%2364748b' stroke-width='2.5' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2'/%3E%3Ccircle cx='12' cy='7' r='4'/%3E%3C/svg%3E"
    lock_svg = "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='18' height='18' viewBox='0 0 24 24' fill='none' stroke='%2364748b' stroke-width='2.5' stroke-linecap='round' stroke-linejoin='round'%3E%3Crect x='3' y='11' width='18' height='11' rx='2' ry='2'/%3E%3Cpath d='M7 11V7a5 5 0 0 1 10 0v4'/%3E%3C/svg%3E"

    st.markdown(f"""
        <style>
        header {{ visibility: hidden; }}
        .block-container {{ max-width: 480px !important; padding-top: 5rem !important; margin: 0 auto !important; }}
        .stApp {{ background-color: #f8fafc; }}
        
        div[data-testid="stVerticalBlockBorderWrapper"] {{
            background-color: #ffffff;
            border: 1px solid #e2e8f0;
            border-radius: 28px !important;
            box-shadow: 0 10px 25px rgba(0, 0, 0, 0.03);
            padding: 2.5rem 2rem !important;
        }}

        .title-text {{ color: #1f7a3f; font-size: 2.0rem !important; font-weight: 800; margin: 0; white-space: nowrap !important; }}
        .label-with-icon {{ color: #475569; display: flex; align-items: center; gap: 8px; font-weight: 700; margin-bottom: 8px; }}
        div[data-testid="stTextInput"] div[data-baseweb="input"] {{ background-color: #f1f5f9; border-radius: 12px !important; }}
        input {{ color: #1e293b; }}

        /* 深色模式适配 + 眼睛补丁 */
        @media (prefers-color-scheme: dark) {{
            .stApp {{ background-color: #0f172a !important; }}
            div[data-testid="stVerticalBlockBorderWrapper"] {{ background-color: #1e293b !important; border: 1px solid #334155 !important; }}
            .title-text {{ color: #4ade80 !important; }}
            .label-with-icon {{ color: #94a3b8 !important; }}
            input {{ color: #f8fafc !important; -webkit-text-fill-color: #f8fafc !important; }}
            div[data-testid="stTextInput"] div[data-baseweb="input"] {{ background-color: #0f172a !important; border: 1px solid #334155 !important; }}
            div[data-testid="stTextInput"] [data-baseweb="input"] > div,
            div[data-testid="stTextInput"] [data-baseweb="input"] button,
            div[data-testid="stTextInput"] [data-baseweb="input"] svg {{ background-color: transparent !important; background: transparent !important; border: none !important; }}
            .stCheckbox label p {{ color: #94a3b8 !important; }}
        }}

        .header-box {{ display: flex; align-items: center; justify-content: center; gap: 12px; margin-bottom: 35px; }}
        .logo-circle {{ background-color: #1f7a3f; color: white; width: 45px !important; height: 45px !important; border-radius: 50% !important; display: flex; align-items: center; justify-content: center; font-size: 28px !important; font-weight: 600 !important; flex-shrink: 0 !important; }}
        
        div.stButton > button {{ background-color: #1f7a3f !important; color: white !important; border-radius: 12px !important; height: 3rem !important; width: 100% !important; border: none !important; transition: all 0.3s ease !important; }}
        
        .custom-error-box {{ background-color: #fee2e2; color: #b91c1c; padding: 10px; border-radius: 10px; text-align: center; margin-bottom: 10px; }}
        @media (prefers-color-scheme: dark) {{ .custom-error-box {{ background-color: #450a0a; color: #fca5a5; }} }}
        
        /* 隐藏下拉框的边框，使其更像一个纯图标按钮 */
        div[data-testid="stSelectbox"] > div {{ border: none !important; background: transparent !important; }}
        </style>
    """, unsafe_allow_html=True)

    with st.container(border=True):
        # --- 语言切换器：CN / EN ---
        cols = st.columns([5.8, 1.2]) # 调整比例给 CN/EN 留出合适空间
        with cols[1]:
            st.selectbox("🌐", ["CN", "EN"], 
                         index=0 if st.session_state.lang == "zh" else 1, 
                         key="lang_sel", 
                         on_change=on_lang_change, 
                         label_visibility="collapsed")

        # 标志与标题
        st.markdown(f'<div class="header-box"><div class="logo-circle">FB</div><h1 class="title-text">{L["title"]}</h1></div>', unsafe_allow_html=True)

        # 账号区域
        st.markdown(f'<div class="label-with-icon"><img src="{user_svg}"> {L["user_label"]}</div>', unsafe_allow_html=True)
        u = st.text_input(L["user_label"], placeholder=L["user_placeholder"], key="user", label_visibility="collapsed")
        
        # 密码区域
        st.markdown(f'<div class="label-with-icon" style="margin-top:10px;"><img src="{lock_svg}"> {L["pwd_label"]}</div>', unsafe_allow_html=True)
        p = st.text_input(L["pwd_label"], placeholder=L["pwd_placeholder"], type="password", key="pwd", label_visibility="collapsed")

        # 记住我
        st.checkbox(L["remember"], value=True)

        # 登录逻辑
        if st.button(L["login_btn"], use_container_width=True):
            if not u or not p:
                st.markdown(f'<div class="custom-error-box">{L["err_empty"]}</div>', unsafe_allow_html=True)
            elif u == "123" and p == "123":
                st.session_state.logged_in = True
                st.rerun()
            else:
                st.markdown(f'<div class="custom-error-box">{L["err_wrong"]}</div>', unsafe_allow_html=True)
