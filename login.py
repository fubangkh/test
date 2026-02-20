import streamlit as st

def show_login_page():
    # 1. 定义灰色 SVG 图标 (统一色系 #64748b, 统一粗细 2.5)
    user_icon = "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='24' height='24' viewBox='0 0 24 24' fill='none' stroke='%2364748b' stroke-width='2.5' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2'/%3E%3Ccircle cx='12' cy='7' r='4'/%3E%3C/svg%3E"
    lock_icon = "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='24' height='24' viewBox='0 0 24 24' fill='none' stroke='%2364748b' stroke-width='2.5' stroke-linecap='round' stroke-linejoin='round'%3E%3Crect x='3' y='11' width='18' height='11' rx='2' ry='2'/%3E%3Cpath d='M7 11V7a5 5 0 0 1 10 0v4'/%3E%3C/svg%3E"

    # 2. 核心 CSS 样式
    st.markdown(f"""
        <style>
        /* 全局背景 */
        .stApp {{ background-color: #f8fafc !important; }}
        
        /* 隐藏 Streamlit 原生页眉 */
        header {{visibility: hidden;}}
        
        /* 登录卡片容器：加大圆角 */
        .block-container {{ 
            max-width: 480px !important; 
            padding-top: 5rem !important; 
        }}
        
        div[data-testid="stVerticalBlockBorderWrapper"] {{
            background-color: white !important;
            border-radius: 28px !important; 
            box-shadow: 0 20px 40px rgba(0, 0, 0, 0.06) !important;
            border: 1px solid #f1f5f9 !important;
            padding: 3rem 2.2rem !important;
        }}

        /* 品牌标题与Logo */
        .brand-logo {{
            background: #1f7a3f; color: white; width: 60px; height: 60px; 
            border-radius: 18px; display: flex; align-items: center; 
            justify-content: center; font-weight: 800; font-size: 1.6rem; 
            box-shadow: 0 8px 16px rgba(31,122,63,0.2); margin: 0 auto 15px;
        }}
        .brand-title {{ 
            color: #064e3b; font-size: 2.2rem; font-weight: 800; 
            text-align: center; margin-bottom: 5px; letter-spacing: -1px;
        }}
        .brand-sub {{ text-align: center; color: #64748b; margin-bottom: 30px; font-size: 0.95rem; }}

        /* --- 彻底消除“套娃”框的核心代码 --- */
        /* 1. 让所有中间层级完全透明，不产生边框和底色 */
        div[data-testid="stTextInput"] div[data-baseweb="input"],
        div[data-testid="stTextInput"] div[data-baseweb="base-input"],
        div[data-testid="stTextInput"] [role="presentation"] {{
            background-color: transparent !important;
            border: none !important;
            box-shadow: none !important;
        }}

        /* 2. 将背景、圆角、图标全部统一在 input 这一层 */
        div[data-testid="stTextInput"] input {{
            background-color: #f1f5f9 !important; /* 统一浅灰色 */
            border: 1px solid #e2e8f0 !important;
            border-radius: 14px !important;
            height: 3.2rem !important;
            padding-left: 3.2rem !important; /* 预留图标空间 */
            background-repeat: no-repeat !important;
            background-position: 1.1rem center !important;
            background-size: 1.25rem !important;
            color: #1e293b !important;
            font-size: 1rem !important;
            transition: all 0.2s;
        }}

        /* 账号图标注入 */
        div[data-testid="stTextInput"]:nth-of-type(1) input {{
            background-image: url("{user_icon}") !important;
        }}
        
        /* 密码图标注入 */
        div[data-testid="stTextInput"]:nth-of-type(2) input {{
            background-image: url("{lock_icon}") !important;
        }}

        /* 密码框右侧按钮（小眼睛）透明化 */
        div[data-testid="stTextInput"] button {{
            background-color: transparent !important;
            border: none !important;
            color: #64748b !important;
        }}

        /* Label 样式 */
        div[data-testid="stTextInput"] label {{
            font-weight: 700 !important;
            color: #334155 !important;
            margin-bottom: 10px !important;
            font-size: 0.95rem !important;
        }}

        /* 立即登录按钮：圆角与高度对齐 */
        div.stButton > button {{
            background-color: #1f7a3f !important;
            color: white !important;
            border-radius: 14px !important;
            height: 3.2rem !important;
            width: 100% !important;
            font-weight: 700 !important;
            font-size: 1.1rem !important;
            border: none !important;
            margin-top: 10px;
            box-shadow: 0 4px 12px rgba(31, 122, 63, 0.2);
        }}
        
        /* 错误提示框对齐 */
        div[data-testid="stNotification"] {{
            border-radius: 14px !important;
            border: none !important;
        }}
        </style>
    """, unsafe_allow_html=True)

    # 3. 页面布局渲染
    with st.container():
        # Logo与标题
        st.markdown("""
            <div class="brand-logo">FB</div>
            <h1 class="brand-title">富邦日记账</h1>
            <p class="brand-sub">管理员授权登录系统</p>
        """, unsafe_allow_html=True)

        # 输入框
        u = st.text_input("账号", placeholder="请输入您的账号", key="user")
        p = st.text_input("密码", placeholder="请输入您的密码", type="password", key="pwd")

        # 辅助功能列
        c1, c2 = st.columns([1, 1])
        with c1:
            st.checkbox("记住我", value=True)
        with c2:
            st.markdown("<div style='text-align:right; padding-top:10px; color:#64748b; font-size:0.9rem; cursor:pointer;'>忘记密码？</div>", unsafe_allow_html=True)

        # 登录按钮
        if st.button("立即登录", use_container_width=True):
            if u == "123" and p == "123":
                st.session_state.logged_in = True
                st.success("验证成功，正在跳转...")
                st.rerun()
            else:
                st.error("账号或密码错误")

        # 底部版权/提示
        st.markdown("<hr style='margin: 25px 0; border:none; border-top:1px solid #f1f5f9;'>", unsafe_allow_html=True)
        st.markdown("""
            <div style='text-align:center; color:#94a3b8; font-size:0.85rem;'>
                💡 忘记密码请联系系统管理员进行重置
            </div>
        """, unsafe_allow_html=True)

# 简单的调用入口测试
if __name__ == "__main__":
    show_login_page()
