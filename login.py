import streamlit as st

def show_login_page():
    # 1. 样式注入：解决居中、间距和 Label 图标显示问题
    st.markdown("""
        <style>
        /* 全局背景 */
        .stApp { background-color: #f8fafc !important; }
        
        /* 页面容器：上移并控制宽度 */
        .block-container { 
            max-width: 500px !important; 
            padding-top: 5rem !important; 
        }

        /* 登录卡片容器（原生 container） */
        div[data-testid="stVerticalBlockBorderWrapper"] {
            background-color: white !important;
            border-radius: 20px !important;
            box-shadow: 0 15px 35px rgba(0,0,0,0.05) !important;
            padding: 2.5rem !important;
            border: 1px solid #edf2f7 !important;
        }

        /* 标题：绿色、加粗、不换行 */
        .main-title {
            color: #166534;
            font-weight: 800;
            font-size: 1.8rem;
            white-space: nowrap;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 12px;
            margin-bottom: 5px;
        }

        /* Label 样式：让 Emoji 和文字对齐 */
        div[data-testid="stTextInput"] label {
            font-weight: 600 !important;
            color: #475569 !important;
            margin-bottom: 8px !important;
            display: flex !important;
            align-items: center !important;
            gap: 8px !important;
        }

        /* 按钮样式 */
        div.stButton > button {
            background-color: #166534 !important;
            color: white !important;
            border-radius: 10px !important;
            height: 3.2rem !important;
            font-weight: 700 !important;
            border: none !important;
            margin-top: 15px;
            transition: all 0.2s ease;
        }
        div.stButton > button:hover {
            background-color: #15803d !important;
            transform: translateY(-1px);
        }

        /* 输入框圆角 */
        div[data-testid="stTextInput"] input {
            border-radius: 8px !important;
        }
        </style>
    """, unsafe_allow_html=True)

    # 2. 居中列布局
    _, col_mid, _ = st.columns([0.1, 0.8, 0.1]) # 进一步收窄中间区域

    with col_mid:
        with st.container(border=True):
            # 顶部标题区
            st.markdown("""
                <div style='text-align: center; margin-bottom: 25px;'>
                    <div class="main-title">📒 富邦日记账</div>
                    <div style='color: #94a3b8; font-size: 0.85rem;'>欢迎回来，请登录您的管理员账号</div>
                </div>
            """, unsafe_allow_html=True)

            # 3. 输入区域：将 Emoji 放在 Label 里
            # 这里通过 st.text_input 的第一个参数传递带图标的 Label
            username = st.text_input("👤 账号", placeholder="请输入账号", key="user")
            
            st.write("") # 增加间距
            
            password = st.text_input("🔒 密码", placeholder="请输入密码", type="password", key="pwd")
            
            # 4. 登录验证
            if st.button("立即安全登录", use_container_width=True):
                if username == "123" and password == "123":
                    st.session_state.logged_in = True
                    st.success("验证成功，正在进入...")
                    st.rerun()
                else:
                    st.error("❌ 账号或密码错误")

            st.divider()
            st.caption("<div style='text-align:center; color:#cbd5e1;'>© 2024 富邦日记账 · 财务管理系统</div>", unsafe_allow_html=True)
