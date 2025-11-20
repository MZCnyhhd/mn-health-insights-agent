import streamlit as st
from datetime import datetime, timedelta
from config.app_config import SESSION_TIMEOUT_MINUTES
import json

class SessionManager:
    """管理用户会话，包括初始化、验证和超时"""
    @staticmethod
    def init_session():
        """初始化或验证会话"""
        # 每个浏览器会话只初始化一次
        if 'session_initialized' not in st.session_state:
            st.session_state.session_initialized = True
            # 尝试从持久化存储中恢复会话
            SessionManager._restore_from_storage()
            
        # 确保关键的会话状态键存在
        if 'user' not in st.session_state:
            st.session_state.user = None
        if 'authenticated' not in st.session_state:
            st.session_state.authenticated = False

        # 初始化认证服务
        if 'auth_service' not in st.session_state:
            from auth.auth_service import AuthService
            st.session_state.auth_service = AuthService()
        
        # 检查会话超时
        if 'last_activity' in st.session_state:
            idle_time = datetime.now() - st.session_state.last_activity
            if idle_time > timedelta(minutes=SESSION_TIMEOUT_MINUTES):
                SessionManager.clear_session_state()
                st.error("会话已过期，请重新登录。")
                st.rerun()
        
        # 更新最后活动时间
        st.session_state.last_activity = datetime.now()
        
        # 当存在已登录用户和令牌时才验证会话
        if st.session_state.user and st.session_state.get('auth_token'):
            user_data = st.session_state.auth_service.validate_session_token()
            if not user_data:
                SessionManager.clear_session_state()
                st.error("无效的会话，请重新登录。")
                st.rerun()
    
    @staticmethod
    def _restore_from_storage():
        """从持久化存储中恢复会话"""
        try:
            # 注入存储脚本以启用localStorage功能
            SessionManager._inject_storage_script()
            
            # 实际的恢复操作在AuthService.try_restore_session()中进行
            # 该方法使用Supabase内置的会话持久化功能
            
        except Exception:
            pass  # 在恢复过程中忽略错误
    
    @staticmethod
    def _inject_storage_script():
        """注入用于持久化存储管理的JavaScript"""
        storage_script = """
        <script>
        // 页面加载时检查localStorage中是否存在用户数据
        window.addEventListener('DOMContentLoaded', function() {
            const storedAuth = localStorage.getItem('hia_auth');
            if (storedAuth) {
                try {
                    const authData = JSON.parse(storedAuth);
                    // 设置一个Python可以检查的标志
                    window.hia_auth_data = authData;
                } catch (e) {
                    localStorage.removeItem('hia_auth');
                }
            }
        });
        
        // 保存认证数据的功能
        window.saveAuthData = function(authData) {
            localStorage.setItem('hia_auth', JSON.stringify(authData));
        };
        
        // 清除认证数据的函数
        window.clearAuthData = function() {
            localStorage.removeItem('hia_auth');
        };
        
        // 获取认证数据的功能
        window.getAuthData = function() {
            const stored = localStorage.getItem('hia_auth');
            return stored ? JSON.parse(stored) : null;
        };
        </script>
        """
        st.markdown(storage_script, unsafe_allow_html=True)

    @staticmethod
    def clear_session_state():
        """清除所有会话状态数据"""
        # 清除持久化存储
        SessionManager._clear_persistent_storage()
        
        # 保留session_initialized键，删除其他所有键
        keys_to_keep = ['session_initialized']
        for key in list(st.session_state.keys()):
            if key not in keys_to_keep:
                del st.session_state[key]
    
    @staticmethod
    def _clear_persistent_storage():
        """清除持久化存储"""
        clear_script = """
        <script>
        if (typeof window.clearAuthData === 'function') {
            window.clearAuthData();
        }
        </script>
        """
        st.markdown(clear_script, unsafe_allow_html=True)
    
    @staticmethod
    def _save_to_persistent_storage(user_data, auth_token):
        """将认证数据保存到持久化存储"""
        auth_data = {
            'user': user_data,
            'auth_token': auth_token,
            'timestamp': datetime.now().isoformat()
        }
        
        save_script = f"""
        <script>
        if (typeof window.saveAuthData === 'function') {{
            window.saveAuthData({json.dumps(auth_data)});
        }}
        </script>
        """
        st.markdown(save_script, unsafe_allow_html=True)

    @staticmethod
    def is_authenticated():
        """检查用户是否已通过身份验证"""
        return bool(st.session_state.get('user'))
    
    @staticmethod
    def create_chat_session():
        """创建新的聊天会话"""
        if not SessionManager.is_authenticated():
            return False, "未通过身份验证"
        return st.session_state.auth_service.create_session(
            st.session_state.user['id']
        )
    
    @staticmethod
    def get_user_sessions():
        """获取用户的聊天会话"""
        if not SessionManager.is_authenticated():
            return False, []
        return st.session_state.auth_service.get_user_sessions(
            st.session_state.user['id']
        )
    
    @staticmethod
    def delete_session(session_id):
        """删除一个聊天会话"""
        if not SessionManager.is_authenticated():
            return False, "未通过身份验证"
        return st.session_state.auth_service.delete_session(str(session_id))
    
    @staticmethod
    def logout():
        """登出用户并清除会话"""
        if 'auth_service' in st.session_state:
            st.session_state.auth_service.sign_out()
        SessionManager.clear_session_state()
    
    @staticmethod
    def login(email, password):
        """处理用户登录"""
        if 'auth_service' not in st.session_state:
            from auth.auth_service import AuthService
            st.session_state.auth_service = AuthService()
            
        success, user_data = st.session_state.auth_service.sign_in(email, password)
        
        # 如果登录成功，则保存到持久化存储
        if success and 'auth_token' in st.session_state:
            SessionManager._save_to_persistent_storage(
                user_data, 
                st.session_state.auth_token
            )
            
        return success, user_data
