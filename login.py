import streamlit as st

def login_page():
    # 居中布局容器
    with st.container():
        st.markdown(f"""
            <style>
            /* 1. 让输入框文字紧贴横线 */
            div[data-testid="stTextInput"] {{
                margin-top: -20px !important; /* 向上提，让输入内容刚好在横线上 */
            }}
            div[data-testid="stTextInput"] input {{
                border-bottom: 2px solid #1F883D !important; /* 横线颜色与按钮一致 */
                border-top: none !important;
                border-left: none !important;
                border-right: none !important;
                background-color: transparent !important;
                border-radius: 0px !important;
                padding-bottom: 2px !important;
                font-size: 1.1rem !important;
            }}
            
            /* 2. 登录按钮自定义样式：初始状态 (深绿) */
            div.stButton > button {{
                background-color: #1F883D !important;
                color: white !important;
                border: none !important;
                transition: all 0.3s ease !important;
                height: 3rem !important;
                font-weight: bold !important;
            }}

            /* 3. 登录按钮悬停状态 (浅绿 + 阴影) */
            div.stButton > button:hover {{
                background-color: #66BB6A !important;
                color: white !important;
                box-shadow: 0 4px 12px rgba(0,0,0,0.2) !important;
                transform: translateY(-1px) !important;
            }}
            
            /* 隐藏标签 */
            div[data-testid="stTextInput"] label {{
                display: none !important;
            }}
            </style>
        """, unsafe_allow_html=True)

        # 更换图标为 📒 (更符合日记账) 或 💰 (财源滚滚)
        st.markdown("## 📒 富邦流水账")
        st.caption("请输入管理员授权的凭证以继续")

        # 输入区域
        st.text_input("用户名", placeholder="👤 请输入账号", key="user")
        st.text_input("密码", placeholder="🔒 请输入密码", type="password", key="pwd")

        # 登录按钮
        if st.button("立即登录", type="primary", use_container_width=True):
                # --- 硬编码验证逻辑 ---
                # 你可以在这里修改你想要的用户名和密码
                if user == "123" and pw == "321":
                    st.session_state.logged_in = True
                    st.success("验证通过，正在加载系统...")
                    st.rerun() # 立即刷新，进入主程序
                else:
                    st.error("❌ 账号或密码不正确")
            
        st.markdown("---")
            st.caption("💡 忘记密码请联系系统管理员")
