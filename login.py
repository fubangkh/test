import streamlit as st

def login_page():
    # 1. 优化 CSS：去掉复杂的 :has 选择器，改用更直接的方式
    st.markdown("""
        <style>
        /* 修改整体背景色（可选，让卡片更突出） */
        .stApp {
            background-color: #f8f9fa;
        }
        
        /* 输入框底线美化 */
        div[data-testid="stTextInput"] input {
            border: none !important;
            border-bottom: 2px solid #e0e0e0 !important;
            border-radius: 0px !important;
            padding: 10px 0px !important;
        }
        
        div[data-testid="stTextInput"] input:focus {
            border-bottom: 2px solid #1F883D !important;
            box-shadow: none !important;
        }

        /* 按钮样式 */
        div.stButton > button {
            background-color: #1F883D !important;
            color: white !important;
            border-radius: 8px !important;
            height: 3.5rem !important;
            font-weight: bold !important;
            border: none !important;
        }
        
        div.stButton > button:hover {
            background-color: #66BB6A !important;
        }
        </style>
    """, unsafe_allow_html=True)

    # 2. 使用 columns 居中
    empty_l, main_col, empty_r = st.columns([1, 2, 1])
    
    with main_col:
        # 使用 st.container(border=True) 代替手动写 div，这样最稳，不会转圈
        with st.container(border=True):
            st.markdown("## 📒 富邦日记账")
            st.caption("请输入管理员授权的凭证以继续")
            
            st.write("") # 间距
            
            # 输入区
            username = st.text_input("用户名", placeholder="👤 账号", key="user", label_visibility="collapsed")
            password = st.text_input("密码", placeholder="🔒 密码", type="password", key="pwd", label_visibility="collapsed")
            
            st.write("")
            
            # 登录逻辑
            if st.button("立即登录", use_container_width=True):
                if username == "123" and password == "321":
                    st.session_state.logged_in = True
                    st.success("验证通过，正在登录...")
                    st.rerun()
                else:
                    st.error("❌ 账号或密码不正确")
            
            st.write("---")
            st.caption("💡 忘记密码请联系管理员")
