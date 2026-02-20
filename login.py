import streamlit as st

def show_login_page():
    # 1. 样式精修：复刻参考图的 SaaS 质感
    st.markdown("""
        <style>
        /* 全局背景色 */
        .stApp { background-color: #f9fafb !important; }

        /* 登录卡片上移与宽度控制 */
        .block-container {
            max-width: 480px !important;
            padding-top: 4rem !important;
        }

        /* 复刻参考图的卡片容器 */
        div[data-testid="stVerticalBlockBorderWrapper"] {
            background-color: white !important;
            border-radius: 16px !important;
            border: 1px solid #e5e7eb !important;
            box-shadow: 0 10px 25px rgba(0, 0, 0, 0.05) !important;
            padding: 2.5rem 1.5rem !important;
        }

        /* 顶部 FB 徽章与标题对齐 */
        .brand-container {
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 12px;
            margin-bottom: 8px;
        }
        .fb-badge {
            background-color: #1f7a3f;
            color: white;
            width: 42px;
            height: 42px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: bold;
            font-size: 1.2rem;
        }
        .brand-title {
            color: #1f7a3f;
            font-size: 2rem;
            font-weight: 700;
            margin: 0;
        }
        .brand-subtitle {
            text-align: center;
            color: #6b7280;
            font-size: 0.95rem;
            margin-bottom: 30px;
        }

        /* 输入框 Label 美化 (复刻灰色图标对齐) */
        div[data-testid="stTextInput"] label {
            font-size: 0.95rem !important;
            color: #374151 !important;
            font-weight: 500 !important;
            margin-bottom: 6px !important;
        }

        /* 输入框内边距与背景 */
        div[data-testid="stTextInput"] input {
            background-color: #fcfcfc !important;
            border: 1px solid #e5e7eb !important;
            border-radius: 10px !important;
            height: 2.8rem !important;
        }

        /* 立即登录按钮 (复刻深绿色与高度) */
        div.stButton > button {
            background-color: #1f7a3f !important;
            color: white !important;
            border-radius: 8px !important;
            height: 3.2rem !important;
            font-size: 1rem !important;
            font-weight: 600 !important;
            border: none !important;
            margin-top: 10px;
            transition: all 0.2s;
        }
        div.stButton > button:hover {
            background-color: #166534 !important;
            box-shadow: 0 4px 12px rgba(31, 122, 63, 0.15) !important;
        }

        /* 底部提示文字 */
        .footer-text {
            font-size: 0.85rem;
            color: #6b7280;
            line-height: 1.5;
            margin-top: 20px;
        }
        </style>
    """, unsafe_allow_html=True)

    # 2. 页面布局
    with st.container(border=True):
        # 复刻参考图顶部：徽章 + 标题
        st.markdown("""
            <div class="brand-container">
                <div class="fb-badge">FB</div>
                <h1 class="brand-title">富邦日记账</h1>
            </div>
            <div class="brand-subtitle">请输入管理员授权的凭证以继续</div>
        """, unsafe_allow_html=True)

        # 3. 输入区域 (Label 使用文本 + 图标组合)
        username = st.text_input("👤 账号", placeholder="请输入账号", key="user")
        password = st.text_input("🔒 密码", placeholder="请输入密码", type="password", key="pwd")

        # 记住我 与 忘记密码 (复刻参考图)
        c1, c2 = st.columns([1, 1])
        with c1:
            st.checkbox("记住我", value=True)
        with c2:
            st.markdown("<div style='text-align:right; padding-top:10px;'><a href='#' style='color:#6b7280; text-decoration:none; font-size:13px;'>忘记密码？</a></div>", unsafe_allow_html=True)

        # 4. 登录验证
        if st.button("立即登录", use_container_width=True):
            if username == "123" and password == "123":
                st.session_state.logged_in = True
                st.success("验证成功")
                st.rerun()
            else:
                st.error("账号或密码错误")

        # 5. 底部页脚
        st.markdown("""
            <hr style='margin: 20px 0; border:none; border-top:1px solid #eee;'>
            <div class="footer-text">提示：这是示例页面，你可以把认证逻辑接到数据库 / API / OAuth。</div>
        """, unsafe_allow_html=True)
