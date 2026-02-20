import streamlit as st

def show_login_page():
    # 1. 样式精修：复刻参考图的 SaaS 风格
    st.markdown("""
        <style>
        /* 全局背景与容器宽度 */
        .stApp { background-color: #f8fafc !important; }
        .block-container { 
            max-width: 520px !important; 
            padding-top: 5rem !important; 
        }

        /* 登录卡片容器（原生 container 增强） */
        div[data-testid="stVerticalBlockBorderWrapper"] {
            background-color: white !important;
            border-radius: 12px !important;
            box-shadow: 0 4px 20px rgba(0,0,0,0.05) !important;
            border: 1px solid #eef2f6 !important;
            padding: 2.5rem 1.8rem !important;
        }

        /* 标题区：FB徽章 + 文字 单行不换行 */
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
            flex-shrink: 0; /* 防止徽章被压缩 */
        }
        .brand-text {
            color: #1f7a3f;
            font-size: 2.2rem;
            font-weight: 700;
            margin: 0;
            white-space: nowrap; /* 绝对禁止换行 */
        }
        .brand-sub {
            text-align: center;
            color: #64748b;
            font-size: 0.95rem;
            margin-bottom: 30px;
        }

        /* 输入框 Label 样式 */
        div[data-testid="stTextInput"] label {
            font-size: 0.95rem !important;
            color: #475569 !important;
            font-weight: 600 !important;
            margin-bottom: 8px !important;
        }

        /* 输入框：背景浅灰，边框极淡 */
        div[data-testid="stTextInput"] input {
            background-color: #f8fafc !important;
            border: 1px solid #e2e8f0 !important;
            border-radius: 8px !important;
            height: 3rem !important;
        }

        /* 登录按钮：深绿背景，无边框 */
        div.stButton > button {
            background-color: #1f7a3f !important;
            color: white !important;
            border-radius: 8px !important;
            height: 3.2rem !important;
            font-size: 1rem !important;
            font-weight: 700 !important;
            border: none !important;
            margin-top: 15px;
        }
        div.stButton > button:hover {
            background-color: #166534 !important;
        }

        /* 记住我 与 忘记密码 对齐微调 */
        .stCheckbox { margin-top: 10px; }
        .forgot-link {
            text-align: right;
            padding-top: 15px;
            color: #64748b;
            font-size: 13px;
        }
        </style>
    """, unsafe_allow_html=True)

    # 2. 页面布局
    with st.container(border=True):
        # 顶部品牌区
        st.markdown("""
            <div class="brand-header">
                <div class="fb-logo">FB</div>
                <h1 class="brand-text">富邦日记账</h1>
            </div>
            <p class="brand-sub">请输入管理员授权的凭证以继续</p>
        """, unsafe_allow_html=True)

        # 3. 输入组件
        username = st.text_input("👤 账号", placeholder="请输入账号 (测试账号:123)", key="user")
        password = st.text_input("🔒 密码", placeholder="请输入密码 (测试密码:123)", type="password", key="pwd")

        # 4. 复刻：记住我 与 忘记密码 布局
        c1, c2 = st.columns([1, 1])
        with c1:
            st.checkbox("记住我", value=True)
        with c2:
            st.markdown("<div class='forgot-link'>忘记密码？</div>", unsafe_allow_html=True)

        # 5. 提交按钮
        if st.button("立即登录", use_container_width=True):
            if username == "123" and password == "123":
                st.session_state.logged_in = True
                st.success("验证成功")
                st.rerun()
            else:
                st.error("❌ 账号或密码错误")

        # 6. 页脚提示
        st.markdown("""
            <hr style='margin: 25px 0; border:none; border-top:1px solid #f1f5f9;'>
            <div style='color: #94a3b8; font-size: 0.85rem; line-height: 1.6;'>
                提示：这是示例页面，你可以把认证逻辑接到数据库 / API / OAuth。
            </div>
        """, unsafe_allow_html=True)
