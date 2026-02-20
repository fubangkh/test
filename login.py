import streamlit as st

def show_login_page():
    # 1. 样式增强：使用 CSS 变量和更精准的选择器
    st.markdown("""
        <style>
        /* 全局背景 */
        .stApp { background-color: #f5f7fb !important; }
        
        /* 强制主容器最大宽度并居中 */
        .block-container {
            max-width: 450px !important;
            padding-top: 5rem !important;
        }

        /* 核心：利用 Streamlit 原生容器模拟卡片 */
        /* 定位最外层的 border 容器并赋予阴影和圆角 */
        div[data-testid="stVerticalBlockBorderWrapper"] {
            background-color: white !important;
            border-radius: 20px !important;
            box-shadow: 0 12px 40px rgba(0,0,0,0.08) !important;
            border: 1px solid #edf2f7 !important;
            padding: 10px !important;
        }

        /* 标题美化 */
        .brand-h2 {
            color: #1f7a3f;
            font-weight: 800;
            text-align: center;
            margin: 0;
            letter-spacing: -0.5px;
        }

        /* 按钮：SaaS 风格 */
        div.stButton > button {
            background-color: #1f7a3f !important;
            color: white !important;
            border-radius: 12px !important;
            height: 3.2rem !important;
            font-weight: 700 !important;
            font-size: 1rem !important;
            border: none !important;
            margin-top: 10px;
            transition: all 0.2s ease;
        }
        div.stButton > button:hover {
            background-color: #166534 !important;
            transform: translateY(-1px);
            box-shadow: 0 4px 12px rgba(31, 122, 63, 0.2) !important;
        }

        /* 修复图标大小差异：强制 placeholder 中的图标大小 */
        input::placeholder {
            font-size: 0.95rem !important;
        }
        /* 针对密码框图标微调 (nth-of-type 逻辑) */
        div[data-testid="stTextInput"]:nth-of-type(2) input::placeholder {
            font-size: 1.1rem !important;
        }
        
        /* 隐藏原生 Label */
        div[data-testid="stTextInput"] label { display: none !important; }
        </style>
    """, unsafe_allow_html=True)

    # 2. 页面内容
    # 使用带边框的容器作为“卡片壳子”
    with st.container(border=True):
        # 顶部品牌区
        st.markdown("""
            <div style='text-align: center; margin-bottom: 25px; margin-top: 10px;'>
                <h2 class="brand-h2">📒 富邦日记账</h2>
                <p style='color: #64748b; font-size: 0.9rem; margin-top: 8px;'>请输入管理员授权的凭证以继续</p>
            </div>
        """, unsafe_allow_html=True)

        # 输入区 - 账号
        # 在图标和提示文字间多加几个空格，视觉上会更整齐
        username = st.text_input("账号", placeholder="👤   请输入账号", key="user")
        
        # 输入区 - 密码
        password = st.text_input("密码", placeholder="🔒   请输入密码", type="password", key="pwd")
        
        st.write("") # 增加一点呼吸间距

        # 3. 登录逻辑 (原生组件，保证响应)
        if st.button("立即登录", use_container_width=True):
            if username == "123" and password == "123":
                st.session_state.logged_in = True
                st.success("登录成功，正在进入系统...")
                st.rerun()
            else:
                st.error("❌ 账号或密码错误")

        st.divider()
        st.caption("💡 忘记密码请联系系统管理员")
