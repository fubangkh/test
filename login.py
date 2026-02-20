import streamlit as st

def show_login_page():
    # 注入 CSS 样式：仅保留按钮美化，移除输入框绿线
    st.markdown("""
        <style>
        /* 1. 按钮样式：深绿底色，白色文字 */
        div.stButton > button {
            background-color: #1F883D !important;
            color: white !important;
            border-radius: 8px !important;
            height: 3rem !important;
            border: none !important;
            margin-top: 10px;
        }
        /* 2. 按钮悬停效果：浅绿 */
        div.stButton > button:hover {
            background-color: #66BB6A !important;
        }
        /* 3. 移除输入框自定义绿线，恢复默认风格 */
        div[data-testid="stTextInput"] input {
            border: 1px solid #dcdfe6 !important; /* 恢复浅灰色边框 */
            border-radius: 4px !important;
        }
        /* 4. 隐藏多余标签 */
        div[data-testid="stTextInput"] label { 
            display: none !important; 
        }
        </style>
    """, unsafe_allow_html=True)

    # 页面居中布局
    _, col_mid, _ = st.columns([1, 2, 1])
    
    with col_mid:
        st.write("###") # 顶部留白
        
        with st.container(border=True):
            # 将主标题从 # 降级为 ##，字体会小一号
            st.markdown("### 📒 富邦日记账")
            st.caption("请输入管理员授权的凭证以继续")

            # 输入区域
            username = st.text_input("用户名", placeholder="👤 请输入账号", key="user")
            password = st.text_input("密码", placeholder="🔒 请输入密码", type="password", key="pwd")
            
            st.write("") # 间距
            
            # 登录验证
            if st.button("立即登录", use_container_width=True):
                if username == "123" and password == "123":
                    st.session_state.logged_in = True
                    st.success("验证通过，正在加载...")
                    st.rerun() 
                else:
                    st.error("❌ 账号或密码不正确")

            st.markdown("---")
            st.caption("💡 忘记密码请联系系统管理员")
