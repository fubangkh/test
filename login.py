import streamlit as st
import time


def show_login_page():
    # ====== 初始化状态 ======
    st.session_state.setdefault("lang", "zh")
    st.session_state.setdefault("logged_in", False)
    st.session_state.setdefault("login_attempted", False)

    # ====== 文案（中英） ======
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
            "empty_both": "请先输入账号和密码",
            "empty_user": "请输入账号",
            "empty_pwd": "请输入密码",
            "wrong": "⚠️ 账号或密码不正确",
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
            "empty_both": "Please enter username and password",
            "empty_user": "Please enter username",
            "empty_pwd": "Please enter password",
            "wrong": "⚠️ Incorrect username or password",
            "lang_label": "Language",
            "lang_zh": "中文",
            "lang_en": "English",
        },
    }[st.session_state.lang]

    # ====== 图标（data URI） ======
    user_svg = "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='18' height='18' viewBox='0 0 24 24' fill='none' stroke='%2364748b' stroke-width='2.5' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2'/%3E%3Ccircle cx='12' cy='7' r='4'/%3E%3C/svg%3E"
    lock_svg = "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='18' height='18' viewBox='0 0 24 24' fill='none' stroke='%2364748b' stroke-width='2.5' stroke-linecap='round' stroke-linejoin='round'%3E%3Crect x='3' y='11' width='18' height='11' rx='2' ry='2'/%3E%3Cpath d='M7 11V7a5 5 0 0 1 10 0v4'/%3E%3C/svg%3E"

    # ====== CSS（只影响登录页） ======
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
            --icon:#64748b;
            --input-bg:#f1f5f9;
            --input-border:#e2e8f0;
            --focus-ring: rgba(31, 122, 63, 0.18);
            --radius-card: 28px;
            --radius-input: 12px;
        }

        [data-testid="stHeader"]{display:none;}
        html{ overflow-y: scroll; }
        .stApp{ background: var(--bg) !important; }

        .block-container{
            max-width: 520px !important;
            padding-top: 2.2rem !important;
            padding-bottom: 2.2rem !important;
            margin: 0 auto !important;
        }

        div[data-testid="stVerticalBlockBorderWrapper"]{
            background: var(--card) !important;
            border: 1px solid var(--card-border) !important;
            border-radius: var(--radius-card) !important;
            box-shadow: 0 10px 25px rgba(0,0,0,0.03);
            padding: 2.0rem 1.6rem !important;
        }

        .header-box{
            display:flex;
            align-items:center;
            justify-content:center;
            gap: 12px;
            margin: 8px 0 8px 0;
            flex-wrap: nowrap !important;
        }
        .logo-circle{
            background: var(--primary);
            color:#fff;
            width: 46px;
            height: 46px;
            border-radius: 50%;
            display:flex;
            align-items:center;
            justify-content:center;
            font-size: 22px;
            font-weight: 900;
            flex-shrink:0;
            box-shadow: 0 8px 18px rgba(31,122,63,0.18);
        }
        .title-text{
            color: var(--primary);
            font-size: 1.95rem;
            font-weight: 900;
            margin: 0;
            white-space: nowrap;
            letter-spacing: -0.5px;
        }
        .subtitle{
            text-align:center;
            color: var(--muted);
            font-weight: 600;
            margin: 6px 0 18px 0;
        }

        .label-with-icon{
            color: var(--muted);
            display:flex;
            align-items:center;
            gap: 8px;
            font-weight: 700;
            margin: 0 0 8px 0;
        }
        .label-with-icon img{ width:18px; height:18px; display:inline-block; }

        /* ===== 你原来的“打通套娃”核心（保留 + 加强） ===== */
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
        div[data-testid="stTextInput"] [data-baseweb="input"] > div > div,
        div[data-testid="stTextInput"] [data-baseweb="input"] span,
        div[data-testid="stTextInput"] [data-baseweb="input"] button,
        div[data-testid="stTextInput"] [data-baseweb="input"] svg{
            background: transparent !important;
            background-color: transparent !important;
            border: none !important;
            box-shadow: none !important;
        }
        div[data-baseweb="input"] input{
            background: transparent !important;
            color: var(--text) !important;
            height: 3.15rem !important;
            line-height: 3.15rem !important;
            padding: 0 52px 0 14px !important;
            font-size: 15px !important;
        }
        div[data-testid="stTextInput"] label{ display:none !important; }

        /* 更轻的提示（不抢眼） */
        .hint{
            margin-top: 10px;
            color: #9a5b13;
            background: rgba(245,158,11,0.10);
            border: 1px solid rgba(245,158,11,0.18);
            border-radius: 12px;
            padding: 10px 12px;
            font-weight: 800;
            text-align: center;
        }

        /* 登录按钮 */
        div.stButton > button{
            background: var(--primary) !important;
            color: #fff !important;
            border-radius: 12px !important;
            height: 3.05rem !important;
            width: 100% !important;
            border: none !important;
            font-weight: 900 !important;
            font-size: 15px !important;
            transition: all 0.2s ease !important;
            cursor: pointer !important;
            margin-top: 12px;
        }
        div.stButton > button:hover{
            background: var(--primary-hover) !important;
            box-shadow: 0 6px 16px rgba(31,122,63,0.18) !important;
            transform: translateY(-1px) !important;
        }
        div.stButton > button:active{
            background: var(--primary-press) !important;
            transform: translateY(1px) !important;
        }

        /* 只用于账号密码错误 */
        .custom-error-box{
            background:#fee2e2;
            color:#b91c1c;
            padding: 12px;
            border-radius: 12px;
            text-align: center;
            font-weight: 900;
        }

        /* “忘记密码？”做成真正链接样式 */
        .forgot-link{
            text-align:right;
            color: var(--muted);
            font-weight: 800;
            cursor: pointer;
            user-select:none;
            padding-top: 6px;
        }
        .forgot-link:hover{
            text-decoration: underline;
        }

        /* 移动端 */
        @media (max-width: 520px){
            .block-container{ padding-top: 1.6rem !important; }
            div[data-testid="stVerticalBlockBorderWrapper"]{
                padding: 1.7rem 1.2rem !important;
                border-radius: 24px !important;
            }
            .title-text{ font-size: 1.65rem !important; }
            .logo-circle{ width:42px; height:42px; font-size:20px; }
            div[data-testid="stTextInput"] div[data-baseweb="input"] > div{ height: 3.0rem !important; }
            div[data-baseweb="input"] input{ height: 3.0rem !important; line-height: 3.0rem !important; font-size: 14.5px !important; }
            div.stButton > button{ height: 3.0rem !important; }
        }

        /* 深色模式 */
        @media (prefers-color-scheme: dark){
            :root{
                --bg:#0f172a;
                --card:#1e293b;
                --card-border:#334155;
                --muted:#94a3b8;
                --text:#f8fafc;
                --input-bg:#0f172a;
                --input-border:#334155;
                --focus-ring: rgba(74,222,128,0.16);
            }
            .title-text{ color:#4ade80 !important; }
            div[data-testid="stVerticalBlockBorderWrapper"]{
                box-shadow: 0 10px 25px rgba(0,0,0,0.28) !important;
            }
            div[data-baseweb="input"] input{
                color: var(--text) !important;
                -webkit-text-fill-color: var(--text) !important;
            }
            .custom-error-box{
                background:#450a0a;
                color:#fca5a5;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # ====== 语言切换 ======
    lang = st.selectbox(
        T["lang_label"],
        options=[("zh", T["lang_zh"]), ("en", T["lang_en"])],
        format_func=lambda x: x[1],
        index=0 if st.session_state.lang == "zh" else 1,
        key="lang_select",
        label_visibility="collapsed",
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
        )

        # 只保留这一条提示（不会重复出现两个）
        show_live_hint = st.session_state.login_attempted or (u != "" or p != "")
        if show_live_hint:
            if not u and not p:
                st.markdown(f'<div class="hint">{T["empty_both"]}</div>', unsafe_allow_html=True)
            elif not u:
                st.markdown(f'<div class="hint">{T["empty_user"]}</div>', unsafe_allow_html=True)
            elif not p:
                st.markdown(f'<div class="hint">{T["empty_pwd"]}</div>', unsafe_allow_html=True)

        # 同一行：记住我 + 忘记密码（右侧“链接”）
        c1, c2 = st.columns([1, 1])
        with c1:
            st.checkbox(T["remember"], value=True)

        with c2:
            # 用一个“隐形按钮”捕获点击，但视觉上是链接
            if st.button(T["forgot"], key="forgot_link_btn", use_container_width=True):
                st.toast(T["forgot_tip"], icon="🔑")
            # 把这个按钮强制变成链接样式 + 右对齐（不再是大绿按钮）
            st.markdown(
                """
                <style>
                button[kind="secondary"][data-testid="baseButton-secondary"][aria-label="忘记密码？"],
                button[kind="secondary"][data-testid="baseButton-secondary"][aria-label="Forgot password?"]{
                    background: transparent !important;
                    border: none !important;
                    box-shadow: none !important;
                    padding: 0 !important;
                    color: var(--muted) !important;
                    font-weight: 800 !important;
                    float: right !important;
                }
                button[kind="secondary"][data-testid="baseButton-secondary"][aria-label="忘记密码？"]:hover,
                button[kind="secondary"][data-testid="baseButton-secondary"][aria-label="Forgot password?"]:hover{
                    text-decoration: underline !important;
                }
                </style>
                """,
                unsafe_allow_html=True,
            )

        # 固定消息槽：只用于“账号密码错误”
        msg_area = st.empty()
        msg_area.markdown("<div style='min-height:52px'></div>", unsafe_allow_html=True)

        clicked = st.button(T["login"], use_container_width=True)

        if clicked:
            st.session_state.login_attempted = True

            # 缺项：只显示 hint，不再额外显示红框
            if not u or not p:
                st.rerun()

            # 登录校验（示例）
            time.sleep(0.2)
            if u == "123" and p == "123":
                st.session_state.logged_in = True
                st.rerun()
            else:
                msg_area.markdown(f'<div class="custom-error-box">{T["wrong"]}</div>', unsafe_allow_html=True)
