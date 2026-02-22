import streamlit as st

def show_login_page():
    # --- 1. 多语言字典 (包含您指定的精准翻译) ---
    LANG_DICT = {
        "zh": {
            "title": "富邦日记账", "user_label": "账号", "user_placeholder": "请输入账号",
            "pwd_label": "密码", "pwd_placeholder": "请输入密码", "remember": "记住我",
            "login_btn": "立即登录", "err_empty": "⚠️ 请先输入账号和密码", "err_wrong": "⚠️ 账号或密码不正确"
        },
        "en": {
            "title": "Fubon Journal", "user_label": "Account", "user_placeholder": "Enter account",
            "pwd_label": "Password", "pwd_placeholder": "Enter password", "remember": "Remember Me",
            "login_btn": "Sign In", "err_empty": "⚠️ Please enter account and password", "err_wrong": "⚠️ Invalid account or password"
        },
        "km": {
            "title": "ហ្វូបង់ សៀវភៅគណនេយ្យ", "user_label": "គណនី", "user_placeholder": "សូមបញ្ចូលគណនី",
            "pwd_label": "លេខសម្ងាត់", "pwd_placeholder": "សូមបញ្ចូលលេខសម្ងាត់", "remember": "ចងចាំខ្ញុំ",
            "login_btn": "ចូលប្រើ", "err_empty": "⚠️ សូមបញ្ចូលគណនី និងលេខសម្ងាត់", "err_wrong": "⚠️ គណនី ឬលេខសម្ងាត់មិនត្រឹមត្រូវ"
        },
        "vi": {
            "title": "Sổ Kế Toán Fubang", "user_label": "Tài khoản", "user_placeholder": "Nhập tài khoản",
            "pwd_label": "Mật khẩu", "pwd_placeholder": "Nhập mật khẩu", "remember": "Ghi nhớ",
            "login_btn": "Đăng nhập", "err_empty": "⚠️ Vui lòng nhập tài khoản và mật khẩu", "err_wrong": "⚠️ Tài khoản hoặc mật khẩu không đúng"
        }
    }

    LANG_MAP = {"中文": "zh", "English": "en", "ភាសាខ្មែរ": "km", "Tiếng Việt": "vi"}
    if 'lang' not in st.session_state: st.session_state.lang = "zh"
    
    def on_lang_change():
        st.session_state.lang = LANG_MAP[st.session_state.lang_sel]

    L = LANG_DICT[st.session_state.lang]

    # SVG 图标
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
            padding: 2.5rem 2.2rem !important; /* 稍微增加左右内边距 */
        }}

        .title-text {{ color: #1f7a3f; font-size: 1.6rem !important; font-weight: 800; margin: 0; white-space: nowrap !important; }}
        .label-with-icon {{ color: #475569; display: flex; align-items: center; gap: 8px; font-weight: 700; margin-bottom: 8px; }}
        
        /* 输入框高度参考：约 45px */
        div[data-testid="stTextInput"] div[data-baseweb="input"] {{ background-color: #f1f5f9; border-radius: 12px !important; }}

        /* --- 修正 1：登录按钮高度变矮，与输入框对齐 --- */
        div.stButton > button {{
            background-color: #1f7a3f !important;
            color: white !important;
            border-radius: 12px !important;
            height: 2.8rem !important; /* 之前是 3rem，现在缩减到 2.8rem 匹配输入框 */
            width: 100% !important;
            border: none !important;
            padding: 0 !important;
            line-height: 2.8rem !important;
            transition: all 0.3s ease !important;
        }}

        /* --- 修正 2：提示框高度变矮 + 位置大幅上移 --- */
        .custom-error-box {{
            background-color: #fee2e2;
            color: #b91c1c;
            padding: 8px 10px !important; /* 减小内边距，压缩高度 */
            border-radius: 10px;
            text-align: center;
            margin-top: -15px !important; /* 大幅负边距，消除空隙，紧贴按钮 */
            font-size: 0.85rem;
            width: 100%;
            box-sizing: border-box;
        }}

        @media (prefers-color-scheme: dark) {{
            .stApp {{ background-color: #0f172a !important; }}
            div[data-testid="stVerticalBlockBorderWrapper"] {{ background-color: #1e293b !important; border: 1px solid #334155 !important; }}
            .title-text {{ color: #4ade80 !important; }}
            div[data-testid="stTextInput"] div[data-baseweb="input"] {{ background-color: #0f172a !important; border: 1px solid #334155 !important; }}
            div[data-testid="stTextInput"] [data-baseweb="input"] > div,
            div[data-testid="stTextInput"] [data-baseweb="input"] button {{ background-color: transparent !important; }}
            .custom-error-box {{ background-color: #450a0a; color: #fca5a5; }}
            .stCheckbox label p {{ color: #94a3b8 !important; }}
        }

        .header-box {{ display: flex; align-items: center; justify-content: center; gap: 12px; margin-bottom: 30px; }}
        .logo-circle {{ background-color: #1f7a3f; color: white; width: 40px; height: 40px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 24px; font-weight: 600; flex-shrink: 0; }}
        </style>
    """, unsafe_allow_html=True)

    with st.container(border=True):
        # 语言切换下拉框
        c1, c2 = st.columns([2.8, 1.2])
        with c2:
            st.selectbox("Lang", list(LANG_MAP.keys()), 
                         index=list(LANG_MAP.values()).index(st.session_state.lang),
                         key="lang_sel", on_change=on_lang_change, label_visibility="collapsed")

        st.markdown(f'<div class="header-box"><div class="logo-circle">FB</div><h1 class="title-text">{L["title"]}</h1></div>', unsafe_allow_html=True)

        st.markdown(f'<div class="label-with-icon"><img src="{user_svg}"> {L["user_label"]}</div>', unsafe_allow_html=True)
        u = st.text_input(L["user_label"], placeholder=L["user_placeholder"], key="user", label_visibility="collapsed")
        
        st.markdown(f'<div class="label-with-icon" style="margin-top:10px;"><img src="{lock_svg}"> {L["pwd_label"]}</div>', unsafe_allow_html=True)
        p = st.text_input(L["pwd_label"], placeholder=L["pwd_placeholder"], type="password", key="pwd", label_visibility="collapsed")

        st.checkbox(L["remember"], value=True)

        # 核心逻辑
        if st.button(L["login_btn"], use_container_width=True):
            if not u or not p:
                st.markdown(f'<div class="custom-error-box">{L["err_empty"]}</div>', unsafe_allow_html=True)
            elif u == "123" and p == "123":
                st.session_state.logged_in = True
                st.rerun()
            else:
                st.markdown(f'<div class="custom-error-box">{L["err_wrong"]}</div>', unsafe_allow_html=True)
