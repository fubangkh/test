import streamlit as st

def show_login_page():
    # 1. 页面居中布局：[左1, 中2, 右1] 比例，让登录框锁死在屏幕中间
    _, col_mid, _ = st.columns([1, 2, 1])
    
    with col_mid:
        # 增加一些顶部间距
        st.write("#", unsafe_allow_html=True)
        
        # 使用带边框的容器，增加“卡片感”
        with st.container(border=True):
            st.markdown("# 📒 富邦日记账")
            st.caption("请输入管理员授权的凭证以继续")

            # 输入框
            username = st.text_input("用户名", placeholder="请输入账号", key="user")
            password = st.text_input("密码", type="password", placeholder="请输入密码", type="password", key="pwd")
            
            # 登录验证
            if st.button("立即登录", use_container_width=True):
                if username == "123" and password == "123":
                    st.session_state.logged_in = True
                    st.success("验证通过，正在加载...")
                    st.rerun() 
                else:
                    st.error("❌ 账号或密码不正确")

            # 5. 脚注
            st.markdown("---")
            st.caption("💡 忘记密码请联系系统管理员")
