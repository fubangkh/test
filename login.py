import streamlit as st
import time

def show_login_page():
    # ====== 初始化状态 ======
    st.session_state.setdefault("lang", "zh")
    st.session_state.setdefault("is_logging_in", False)
    st.session_state.setdefault("logged_in", False)
    st.session_state.setdefault("login_attempted", False)

    T = {
        "zh": {
            "app_title": "富邦日记账",
            "subtitle": "管理员授权登录",
            "account": "账号",
            "password": "密码",
            "remember": "记住我",
            "forgot": "忘记密码？",
            "forgot_tip": "请联系系统管理员重置密码。",
            "login": "立即登录",
            "logging": "登录中…",
            "empty_both": "请先输入账号和密码",
            "empty_user": "请输入账号",
            "empty_pwd": "请输入密码",
            "wrong": "⚠️ 账号或密码不正确",
            "success": "登录成功",
            "lang_label": "语言",
            "lang_zh": "中文",
            "lang_en": "English",
        },
        "en": {
            "app_title": "FUBANG Ledger",
            "subtitle": "Admin Authorized Login",
            "account": "Username",
            "password": "Password",
            "remember": "Remember me",
            "forgot": "Forgot password?",
            "forgot_tip": "Please contact the system administrator to reset your password.",
            "login": "Sign in",
            "logging": "Signing in…",
            "empty_both": "Please enter username and password",
            "empty_user": "Please enter username",
            "empty_pwd": "Please enter password",
            "wrong": "⚠️ Incorrect username or password",
            "success": "Signed in successfully",
            "lang_label": "Language",
            "lang_zh": "中文",
            "lang_en": "English",
        },
    }[st.session_state.lang]

    # ====== SVG 图标（data URI） ======
    user_svg = "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='18' height='18' viewBox='0 0 24 24' fill='none' stroke='%2364748b' stroke-width='2.5' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2'/%3E%3Ccircle cx='12' cy='7' r='4'/%3E%3C/svg%3E"
    lock_svg = "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='18' height='18' viewBox='0 0 24 24' fill='none' stroke='%2364748b' stroke-width='2.5' stroke-linecap='round' stroke-linejoin='round'%3E%3Crect x='3' y='11' width='18' height='11' rx='2' ry='2'/%3E%3Cpath d='M7 11V7a5 5 0 0 1 10 0v4'/%3E%3C/svg%3E"

    # ✅ 关键：CSS 必须在 st.markdown 里 + unsafe_allow_html=True + 只有 <style> 内容
    st.markdown(
        """
        <style>
        :root{
            --primary:#1f7a3f;
            --primary-hover:#2d9a50;
            --primary-press:#165c2f;

            --bg:#f8fafc;
            --card:#ffffff;
            --card-border:#e2e8f0;

            --muted:#475569;
            --text:#1e293b;

            --input-bg:#f1f5f9;
            --input-border:#e2e8f0;
            --focus-ring: rgba(31, 122, 63, 0.18);

            --radius-card: 28px;
            --radius-input: 12px;
        }

        html{ overflow-y: scroll; }
        .stApp{ background: var(--bg) !important; }

        .block-container{
            max-width: 520px !important;
            padding-top: 3.2rem !important;
            padding-bottom: 2.2rem !important;
            margin: 0 auto !important;
        }

        /* 卡片 */
        div[data-testid="stVerticalBlockBorderWrapper"]{
            background: var(--card) !important;
            border: 1px solid var(--card-border) !important;
            border-radius: var(--radius-card) !important;
            box-shadow: 0 10px 25px rgba(0,0,0,0.03);
            padding: 2.2rem 2rem !important;
        }

        /* 标题 */
        .header-box{
            display:flex; align-items:center; justify-content:center;
            gap:12px; margin-bottom:10px; flex-wrap:nowrap;
        }
        .logo-circle{
            background: var(--primary);
            color:#fff;
            width:46px; height:46px;
            border-radius:50%;
            display:flex; align-items:center; justify-content:center;
            font-size:22px; font-weight:900;
            flex-shrink:0;
            box-shadow: 0 8px 18px rgba(31,122,63,0.18);
        }
        .title-text{
            color: var(--primary);
            font-size: 1.95rem;
            font-weight: 900;
            margin:0;
            white-space:nowrap;
            letter-spacing:-0.5px;
        }
        .subtitle{
            text-align:center;
            color: var(--muted);
            font-weight:600;
            margin: 6px 0 18px 0;
        }

        /* label */
        .label-with-icon{
            color: var(--muted);
            display:flex; align-items:center;
            gap:8px;
            font-weight:700;
            margin: 0 0 8px 0;
        }
        .label-with-icon img{ width:18px; height:18px; display:inline-block; }

        /* 输入框：打通套娃 + focus */
        div[data-testid="stTextInput"] div[data-baseweb="input"] > div{
            background: var(--input-bg) !important;
            border: 1px solid var(--input-border) !important;
            border-radius: var(--radius-input) !important;
            height: 3.15rem !important;
            display:flex !important;
            align-items:center !important;
            overflow:hidden !important;
            box-shadow:none !important;
            transition: box-shadow .15s ease, border-color .15s ease;
        }
        div[data-testid="stTextInput"] div[data-baseweb="input"]:focus-within > div{
            border-color: rgba(31,122,63,0.55) !important;
            box-shadow: 0 0 0 4px var(--focus-ring) !important;
        }

        div[data-baseweb="input"] > div > div{
            background: transparent !important;
            border:none !important;
            box-shadow:none !important;
        }
        div[data-baseweb="input"] > div > div::before,
        div[data-baseweb="input"] > div > div::after{
            content:none !important;
            display:none !important;
        }

        div[data-baseweb="input"] input{
            background: transparent !important;
            color: var(--text) !important;
            height: 3.15rem !important;
            line-height: 3.15rem !important;
            padding: 0 52px 0 14px !important;
            font-size: 15px !important;
        }

        div[data-baseweb="input"] button,
        div[data-baseweb="input"] [role="button"]{
            background: transparent !important;
            border:none !important;
            box-shadow:none !important;
        }
        div[data-testid="stTextInput"] label{ display:none !important; }

        /* hint */
        .hint{
            margin-top:8px;
            color:#b45309;
            background: rgba(245,158,11,0.12);
            border: 1px solid rgba(245,158,11,0.22);
            border-radius:12px;
            padding:10px 12px;
            font-weight:700;
            text-align:center;
        }

        /* checkbox */
        div[data-testid="stCheckbox"] label p{
            color: var(--muted) !important;
            font-weight: 600 !important;
        }
        div[data-testid="stCheckbox"] input[type="checkbox"]{
            accent-color: var(--primary) !important;
        }

        /* 登录按钮（只做登录页用：通过 key 限定） */
        div[data-testid="stButton"] button[data-testid="baseButton-primary"]{
            background: var(--primary) !important;
            color:#fff !important;
            border-radius:12px !important;
            height:3.05rem !important;
            width:100% !important;
            border:none !important;
            font-weight:800 !important;
            font-size:15px !important;
            transition: all .2s ease !important;
            cursor:pointer !important;
            margin-top:10px;
        }
        div[data-testid="stButton"] button[data-testid="baseButton-primary"]:hover{
            background: var(--primary-hover) !important;
            box-shadow: 0 6px 16px rgba(31,122,63,0.18) !important;
            transform: translateY(-1px) !important;
        }

        .custom-error-box{
            background:#fee2e2;
            color:#b91c1c;
            padding:12px;
            border-radius:12px;
            text-align:center;
            font-weight:800;
        }

        /* 移动端 */
        @media (max-width: 520px){
            .block-container{ padding-top: 1.8rem !important; }
            div[data-testid="stVerticalBlockBorderWrapper"]{
                padding: 1.8rem 1.25rem !important;
                border-radius: 24px !important;
            }
            .title-text{ font-size: 1.65rem !important; }
            .logo-circle{ width:42px; height:42px; font-size:20px; }
            div[data-testid="stTextInput"] div[data-baseweb="input"] > div{ height: 3.0rem !important; }
            div[data-baseweb="input"] input{ height: 3.0rem !important; line-height: 3.0rem !important; font-size: 14.5px !important; }
        }

        /* 深色模式 */
        @media (prefers-color-scheme: dark){
            .stApp { background: #0f172a !important; }
            div[data-testid="stVerticalBlockBorderWrapper"]{
                background:#1e293b !important;
                border:1px solid #334155 !important;
                box-shadow: 0 10px 25px rgba(0,0,0,0.28) !important;
            }
            .title-text{ color:#4ade80 !important; }
            .subtitle{ color:#94a3b8 !important; }
            .label-with-icon{ color:#94a3b8 !important; }
            div[data-testid="stTextInput"] div[data-baseweb="input"] > div{
                background:#0f172a !important;
                border:1px solid #334155 !important;
            }
            div[data-baseweb="input"] input{
                color:#f8fafc !important;
                -webkit-text-fill-color:#f8fafc !important;
            }
            .custom-error-box{ background:#450a0a; color:#fca5a5; }
            .hint{
                color:#fdba74;
                background: rgba(245,158,11,0.10);
                border: 1px solid rgba(245,158,11,0.22);
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # ✅ 调试用这句你看到了就证明代码生效；确认正常后删掉
    st.caption("LOGIN UPDATED ✅")

    # 语言切换
    c_lang1, c_lang2 = st.columns([1, 1])
    with c_lang1:
        st.write("")
    with c_lang2:
        lang = st.selectbox(
            T["lang_label"],
            options=[("zh", T["lang_zh"]), ("en", T["lang_en"])],
            format_func=lambda x: x[1],
            index=0 if st.session_state.lang == "zh" else 1,
            key="lang_select",
            label_visibility="collapsed",
            disabled=st.session_state.is_logging_in,
        )
        if lang[0] != st.session_state.lang:
            st.session_state.lang = lang[0]
            st.rerun()

    with st.container(border=True):
        st.markdown(
            f'<div class="header-box"><div class="logo-circle">FB</div><h1 class="title-text">{T["app_title"]}</h1></div>'
            f'<div class="subtitle">{T["subtitle"]}</div>',
            unsafe_allow_html=True,
        )

        st.markdown(f'<div class="label-with-icon"><img src="{user_svg}"> {T["account"]}</div>', unsafe_allow_html=True)
        u = st.text_input(
            T["account"],
            placeholder="123" if st.session_state.lang == "en" else "请输入账号，测试账号123",
            key="user",
            label_visibility="collapsed",
            disabled=st.session_state.is_logging_in,
        )

        st.markdown(
            f'<div class="label-with-icon" style="margin-top:12px;"><img src="{lock_svg}"> {T["password"]}</div>',
            unsafe_allow_html=True,
        )
        p = st.text_input(
            T["password"],
            placeholder="123" if st.session_state.lang == "en" else "请输入密码，测试密码123",
            type="password",
            key="pwd",
            label_visibility="collapsed",
            disabled=st.session_state.is_logging_in,
        )

        show_live_hint = st.session_state.login_attempted or (u != "" or p != "")
        live_hint = ""
        if show_live_hint:
            if not u and not p:
                live_hint = T["empty_both"]
            elif not u:
                live_hint = T["empty_user"]
            elif not p:
                live_hint = T["empty_pwd"]
        if live_hint:
            st.markdown(f'<div class="hint">{live_hint}</div>', unsafe_allow_html=True)

        c1, c2 = st.columns([1, 1])
        with c1:
            st.checkbox(T["remember"], value=True, disabled=st.session_state.is_logging_in)
        with c2:
            # 右对齐的“忘记密码？”
            st.markdown("<div style='display:flex;justify-content:flex-end;'>", unsafe_allow_html=True)
            if st.button(T["forgot"], key="forgot_pwd_btn", disabled=st.session_state.is_logging_in):
                st.info(T["forgot_tip"])
            st.markdown("</div>", unsafe_allow_html=True)

        # 消息槽固定高度
        msg_area = st.empty()
        msg_area.markdown("<div style='min-height:56px'></div>", unsafe_allow_html=True)

        login_label = T["logging"] if st.session_state.is_logging_in else T["login"]
        clicked = st.button(login_label, use_container_width=True, disabled=st.session_state.is_logging_in)

        if clicked:
            st.session_state.login_attempted = True
            if not u or not p:
                msg_area.markdown(f'<div class="custom-error-box">{T["empty_both"]}</div>', unsafe_allow_html=True)
            else:
                st.session_state.is_logging_in = True
                st.rerun()

        if st.session_state.is_logging_in:
            with st.spinner(T["logging"]):
                time.sleep(0.6)

            if u == "123" and p == "123":
                st.session_state.logged_in = True
                st.session_state.is_logging_in = False
                st.success(T["success"])
                st.rerun()
            else:
                st.session_state.is_logging_in = False
                msg_area.markdown(f'<div class="custom-error-box">{T["wrong"]}</div>', unsafe_allow_html=True)
